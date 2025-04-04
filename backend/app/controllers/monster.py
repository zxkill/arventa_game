import json

from app.repositories.ItemRepository import ItemRepository
from app.repositories.MonsterRepository import MonsterRepository
from app.repositories.PlayerItemProgressRepository import PlayerItemProgressRepository
from app.repositories.PointRepository import PointRepository
from app.config.config import logger, redis, asyncRedis
from app.repositories.UserItemRepository import UserItemRepository
from app.repositories.UserRepository import UserRepository
from app.services.ActionsEvent import ActionsEvent
from app.services.Battle import calculate_damage
from app.services.QuestEvent import handle_event, QuestEvent
from app.utils.Json import format_error_response
from app.services.maps import check_range
from app.services.Character import Character
from app.utils.Item import check_item_drops
from app.utils.User import get_items_data, is_overload

cache_ttl = 20


async def fetch_monster_data(monster_id: int, db, current_user):
    """Получение и проверка данных ресурса и точки."""
    monster_id = int(monster_id)
    if not monster_id:
        return format_error_response("Такого объекта не существует")
    pointRep = PointRepository(db)
    point = await pointRep.get_point_by_id(monster_id)
    if not point or point['type'] != 'monsters':
        return None, "Такого объекта не существует"

    if not check_range(point['lon'], point['lat'], current_user):
        return None, "Подойдите ближе для взаимодействия"

    if await is_overload(db, current_user):
        return None, "У вас перегруз. Избавьтесь от лишних предметов"

    monster = await MonsterRepository(db).get_monster_by_id(point['object_id'])
    monster['monster_id'] = monster['id']
    monster['id'] = point['id']  # хак, чтобы у монстров на карте были уникальные айди
    if not monster:
        return None, "Такого объекта не существует"

    return {
        'point': point,
        'monster': monster
    }, None

async def monster_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'get': get_monster,
        'fight_start': fight_start,
        'monster_attack': monster_attack
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def get_monster(body, db, current_user):
    monster_id = int(body['monster_id'].split("p")[1])
    logger.debug(f"monster_id: {monster_id}")
    if not monster_id:
        return format_error_response("Такого объекта не существует")

    monster_data, error_message = await fetch_monster_data(monster_id, db, current_user)
    if error_message:
        return format_error_response(error_message)

    monster = monster_data['monster']
    monster = Character(monster, None, 'monster')
    return {
        "success": True,
        "data": {
            'name': monster.character_data['name'],
            'description': monster.character_data['description'],
            'health': monster.get_cur_health(),
            'max_health': monster.get_max_health(),
            'loot': json.loads(monster.get_loot()),
        },
        "message": None,
        "successMessage": None
    }


async def fight_start(body, db, current_user):
    monster_id = int(body['monster_id'].split("p")[1])
    monster_data, error_message = await fetch_monster_data(monster_id, db, current_user)
    if error_message:
        return format_error_response(error_message)

    cache_key = f"point.used:{monster_id}"
    cache_key_user = f"point.used:{monster_id}:user.id:{current_user['id']}"
    already_fight = redis.get(cache_key)
    logger.debug(f"already_fight={already_fight}")
    if already_fight:
        return format_error_response("Объект пока недоступен")

    logger.debug(f"monster_data: {monster_data}")
    # запишем в редис, что кто-то начал бить этого монстра, пока не выйдет таймаут - его нельзя бить
    # ставим на 20 секунд, после каждого удара будем обновлять
    await asyncRedis.setex(cache_key, cache_ttl, 1)
    logger.debug(f"после записи в редис")
    # и привязываем к пользователю, чтобы никто другой не смог продолжить битву или получить награду
    await asyncRedis.setex(cache_key_user, cache_ttl, 1)
    return {
        "success": True,
        "data": {'fight': True},
        "message": None,
        "successMessage": None
    }


async def monster_attack(body, db, current_user):
    monster_id = int(body['monster_id'].split("p")[1])
    monster_data, error_message = await fetch_monster_data(monster_id, db, current_user)
    if error_message:
        return format_error_response(error_message)

    # если есть запись в редис об этом монстре для этого пользователя, то мы можем его бить
    cache_key = f"point.used:{monster_id}"
    cache_key_user = f"point.used:{monster_id}:user.id:{current_user['id']}"
    access_fight = await asyncRedis.get(cache_key_user)
    logger.debug(f"access_fight={access_fight}")
    if not access_fight:
        return {
            "success": False,
            "data": None,
            "message": "Вам нельзя его бить",
            "successMessage": None
        }

    items_data = await get_items_data(db, current_user)

    player = Character(current_user, items_data)
    logger.debug(f"player: {player}")
    monster = Character(monster_data['monster'], None, 'monster')

    logger.debug(f"monster: {monster}")

    # рассчитываем сражение
    # сперва игрок бьет монстра todo в дальнейшем очередность удара над рассчитывать исходя из скорости
    damage_to_monster, critical = calculate_damage(player, monster)
    if not monster.take_damage(damage_to_monster, player.get_accuracy()):
        damage_to_monster = 0

    # монстр побежден
    if monster.get_cur_health() <= 0:
        # если монстр побежден, то удалим запись о нашей битве
        await asyncRedis.delete(cache_key_user)
        # и выставим общий таймер на респаун
        await asyncRedis.setex(cache_key, monster_data['monster']['cooldown_seconds'], 1)
        # сбросим состояние монстра, чтобы все его показатели восстановились
        monster.reset_character_state()
        # событие для отслеживания квестов
        event = QuestEvent(action='kill', target_id=monster.character_data['monster_id'], quantity=1, user_id=current_user['id'])
        await handle_event(event, db)

        await ActionsEvent(action='kill', user_id=current_user['id']).handle_event()

        async with db.transaction():
            # обновим опыт использования оружия и брони
            type_resource_type = {}
            for item_data in items_data:
                if item_data['is_equipped']:
                    experience = 3 # todo тут можно подумать над прогрессивной шкалой
                    if not item_data['type'] in type_resource_type and not item_data['resource_type'] in item_data['type']:
                        type_resource_type[item_data['type']] = item_data['resource_type']
                        await PlayerItemProgressRepository(db).update_progress(current_user['id'], item_data['type'], experience, item_data['resource_type'])
            reward = json.loads(monster.get_loot())
            # Начисление денег
            silver_reward = int(reward.get('money', {}).get('silver', 0))
            if silver_reward > 0:
                if not await UserRepository(db).update_silver(current_user['id'], silver_reward):
                    return {
                        "success": False,
                        "data": None,
                        "message": "Не удалось начислить серебро.",
                        "successMessage": None
                    }
            # Начисление предметов
            items_ids = []
            user_item_rep = UserItemRepository(db)
            for item in reward.get("items", []):
                # рассчитаем шанс, что мы получили предмет
                if await check_item_drops(item, items_data, db, current_user):
                    items_ids.append(item['id'])
                    if not await user_item_rep.add_item(
                            current_user['id'],
                            item["id"],
                            item["quantity"]
                    ):
                        return {
                            "success": False,
                            "data": None,
                            "message": "Ошибка добавления предмета.",
                            "successMessage": None
                        }
            if items_ids is not None:
                items_data = await ItemRepository(db).get_items_by_id(items_ids)

        return {
            "success": True,
            "data": {
                'damage_to_monster': damage_to_monster,
                'new_health_monster': monster.get_cur_health(),
                'reward': {
                    'silver': silver_reward,
                    'items': items_data
                },
                'status': 'victory'
            },
            "message": None,
            "successMessage": None
        }

    # теперь ходит монстр
    damage_to_player, critical = calculate_damage(monster, player)
    if not player.take_damage(damage_to_player, monster.get_accuracy()):
        damage_to_player = 0

    # проиграли
    # todo надо подумать над санкциями
    if player.get_cur_health() <= 0:
        # если проиграли, то удалим запись о нашей битве
        await asyncRedis.delete(cache_key_user)
        # и удалим запись и битве с этим монстром, чтобы любой мог начать с ним битву
        await asyncRedis.delete(cache_key)
        return {
            "success": True,
            "data": {
                'damage_to_monster': damage_to_monster,
                'damage_to_player': damage_to_player,
                'new_health_monster': monster.get_cur_health(),
                'status': 'defeat'
            },
            "message": None,
            "successMessage": None
        }

    # если здоровье у всех еще есть, то продолжаем бой
    # и обновим записи в редис, чтобы они не протухли раньше времени и не сломали текущий бой
    await asyncRedis.setex(cache_key, cache_ttl, 1)
    await asyncRedis.setex(cache_key_user, cache_ttl, 1)
    return {
        "success": True,
        "data": {
            'damage_to_monster': damage_to_monster,
            'damage_to_player': damage_to_player,
            'new_health_monster': monster.get_cur_health(),
            'status': 'fight'
        },
        "message": None,
        "successMessage": None
    }
