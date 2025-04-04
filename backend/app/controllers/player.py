import json
import re
from datetime import datetime

from app.config.config import logger, asyncRedis, PLAYER_COORDS_TTL, SEARCH_RADIUS
from app.repositories.ItemRepository import ItemRepository
from app.repositories.PlayerItemProgressRepository import PlayerItemProgressRepository
from app.repositories.UserItemRepository import UserItemRepository
from app.repositories.UserProfileRepository import UserProfileRepository
from app.repositories.UserRepository import UserRepository
from app.services.Character import Character
from app.services.users import get_player_coords, get_interaction_radius
from app.utils.Json import format_error_response
from app.tasks import save_coords_to_db
from app.utils.User import get_items_data


async def player_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'update_coordinates': update_coordinates,
        'get_nearby_players': get_nearby_players,
        'get_player_info': get_player_info,
        'item_equip': item_equip,
        'user_item_delete': user_item_delete,
        'find_users': find_users,
        'get_self': get_self
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def update_coordinates(body, db, current_user):
    longitude = body['longitude']
    latitude = body['latitude']
    # Сохраняем координаты в Redis
    # logger.info('Метод /coordinates. Пользователь: ' + str(current_user['id']))
    if longitude:
        await asyncRedis.geoadd("players:locations", (longitude, latitude, current_user['id']))
        # Создаем отдельный ключ с TTL для отслеживания "свежести"
        await asyncRedis.set(f"player_last_seen:{current_user['id']}", 0, ex=PLAYER_COORDS_TTL)
        save_coords_to_db.delay(current_user['id'], longitude, latitude)
        return {
            "success": True,
            "data": None,
            "message": None,
            "successMessage": None
        }
    return {
        "success": False,
        "data": None,
        "message": None,
        "successMessage": None
    }


async def get_nearby_players(body, db, current_user):
    """
    Возвращает список игроков в радиусе
    """
    player_coords = get_player_coords(current_user)
    # logger.info('Response nearbyPlayers user id: ' + pprint.pformat(current_user['id']))
    if not player_coords:
        return {"error": "Player not found"}

    lon, lat = player_coords

    # Получаем игроков в радиусе
    nearby_players = await asyncRedis.georadius(
        "players:locations", float(lon), float(lat), SEARCH_RADIUS, unit="m", withdist=False, withcoord=True
    )

    # Исключаем самого игрока
    for x in nearby_players:
        if x[0] == str(current_user['id']):
            nearby_players.remove(x)

    # Фильтруем только активных игроков
    active_players = []
    for playerId, coord in nearby_players:
        if await asyncRedis.exists(f"player_last_seen:{playerId}"):
            active_players.append({
                "player_id": playerId,
                "latitude": coord[1],
                "longitude": coord[0]
            })

    return {
        "success": True,
        "data": active_players,
        "message": None,
        "successMessage": None
    }


async def get_self(body, db, current_user):
    # Получение предметов пользователя
    items_data = await get_items_data(db, current_user)

    user_helper = Character(current_user, items_data)
    logger.debug(f"user_helper={user_helper}")
    user_attributes = user_helper.get_attributes()
    logger.debug(f"items_data: {items_data}")
    settings = json.loads(await UserProfileRepository(db).get_settings(current_user["id"]))
    profile = await UserProfileRepository(db).get_profile(current_user["id"])
    ALL_SKILLS = [
        {"type_item": "weapon", "type_resource": "ore"},
        {"type_item": "weapon", "type_resource": "wood"},
        {"type_item": "armor", "type_resource": "skin"},
        {"type_item": "armor", "type_resource": "ore"},
        {"type_item": "armor", "type_resource": "cloth"},
        {"type_item": "tool", "type_resource": "ore"},
        {"type_item": "tool", "type_resource": "wood"},
        {"type_item": "tool", "type_resource": "skin"},
        {"type_item": "craft", "type_resource": "ore"},
        {"type_item": "craft", "type_resource": "wood"},
        {"type_item": "craft", "type_resource": "skin"},
        {"type_item": "craft", "type_resource": "cloth"},
    ]
    skill_progress = []
    items_progress = await PlayerItemProgressRepository(db).get_current_progress(current_user["id"])
    # Преобразуем список из БД в словарь для быстрого поиска
    progress_dict = {
        (item["type_item"], item["type_resource"]): item for item in items_progress
    }
    for item in ALL_SKILLS:
        key = (item["type_item"], item["type_resource"])
        if key in progress_dict:
            # Если предмет найден в базе, используем его данные
            item_data = progress_dict[key]
            skill_progress.append({
                "type_item": item_data["type_item"],
                "type_resource": item_data["type_resource"],
                "current_level": item_data["current_level"],
                "current_experience": item_data["current_experience"],
                "experience_required": item_data["experience_required"],
            })
        else:
            # Если предмета нет в базе, устанавливаем уровень 1 и 0 опыта
            skill_progress.append({
                "type_item": item["type_item"],
                "type_resource": item["type_resource"],
                "current_level": 1,
                "current_experience": 0,
                "experience_required": 100,  # Установи значение по умолчанию
            })

    return {
        "success": True,
        "data": {
            "id": current_user["id"],
            "name": current_user["username"],
            "silver": current_user["silver"],
            'settings': settings,
            'profile': profile,
            "interaction_radius": get_interaction_radius(current_user),
            "items": items_data,
            "attributes": user_attributes,
            'skill_progress': skill_progress
        },
        "message": None
    }


async def get_player_info(body, db, current_user):
    player_id = int(body['player_id'])
    logger.info(f"player id {player_id}")
    if not player_id:
        user = current_user
    else:
        query = "SELECT * FROM users WHERE id = $1"
        user = await db.fetchrow(query, player_id)
    profile = await UserProfileRepository(db).get_profile(user["id"])
    if 'birthday' in profile and profile['birthday'] is not None:
        birthday_date = datetime.strptime(profile["birthday"], '%Y-%m-%d')
        formatted_birthday = birthday_date.strftime('%d.%m.%Y')
    else:
        formatted_birthday = None
    logger.info(f"user {user}")
    return {
        "success": True,
        "data": {
            "id": user["id"],
            "username": user["username"],
            'avatar': profile["avatar"],
            'name': profile["name"],
            'birthday': formatted_birthday,
            'bio': profile["bio"],
            'register': user['created_at'].strftime("%d.%m.%Y"),
        },
        "message": None,
        "successMessage": None
    }


async def item_equip(body, db, current_user):
    user_item_id = body['user_item_id']
    user_item_id = int(user_item_id)
    if not user_item_id:
        return {
            "success": False,
            "data": None,
            "message": 'Не указан предмет',
            "successMessage": None
        }
    # проверим, чтобы предмет был у этого игрока и проверим, чтобы этот предмет можно было надевать
    user_item = await UserItemRepository(db).get_user_item_by_id(user_item_id, current_user["id"])
    if not user_item or not await ItemRepository(db).is_equippetable(user_item['item_id']):
        return {
            "success": False,
            "data": None,
            "message": 'Невозможно надеть/снять этот предмет',
            "successMessage": None
        }
    # а еще надо проверить доступен ли нам такой уровень предмета
    logger.debug(f"user_item {user_item}")
    item_data = await ItemRepository(db).get_items_by_id([user_item['item_id']])
    item_progress = await PlayerItemProgressRepository(db).get_current_level_for_item(current_user["id"],
                                                                                      item_data[0]['type'],
                                                                                      item_data[0]['resource_type'])
    if (item_progress is None and item_data[0]['tier'] > 1) or (
            item_progress is not None and item_progress['current_level'] < item_data[0]['tier']):
        return {
            "success": False,
            "data": None,
            "message": 'Вы пока не можете это надеть',
            "successMessage": None
        }
    # все проверки прошли, пометим предмет как экипированный
    if not await UserItemRepository(db).equip(user_item_id, user_item['item_id'], current_user['id']):
        return {
            "success": False,
            "data": None,
            "message": 'Ошибка. Попробуйте снова',
            "successMessage": None
        }

    return {
        "success": True,
        "data": {'equipped': True},
        "message": None,
        "successMessage": None
    }


async def user_item_delete(body, db, current_user):
    user_item_id = int(body['user_item_id'])
    count = int(body['count'])
    if not user_item_id:
        return {
            "success": False,
            "data": None,
            "message": 'Не указан предмет',
            "successMessage": None
        }
    # проверим, чтобы предмет был у этого игрока
    user_item = await UserItemRepository(db).get_user_item_by_id(user_item_id, current_user["id"])
    if not user_item or user_item['quantity'] < count:
        return {
            "success": False,
            "data": None,
            "message": 'Невозможно уничтожить этот предмет',
            "successMessage": None
        }
    # все проверки прошли, уничтожаем
    if not await UserItemRepository(db).destroy(user_item_id, user_item['quantity'], count):
        return {
            "success": False,
            "data": None,
            "message": 'Ошибка. Попробуйте снова',
            "successMessage": None
        }

    return {
        "success": True,
        "data": None,
        "message": None,
        "successMessage": None
    }


async def find_users(body, db, current_user):
    query = body.get('query')
    if not query or not isinstance(query, str):
        format_error_response('Не верный запрос')

    # Обрезаем лишние пробелы
    query = query.strip()
    if len(query) < 2 or len(query) > 20 or not re.match(r'^[\w\s]+$', query):
        format_error_response(None)
    users = await UserRepository(db).find_by_username(body['query'])
    return {
        "success": True,
        "data": [{"id": user['id'], "username": user['username']} for user in users if users],
        "message": None,
        "successMessage": None
    }
