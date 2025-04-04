import json
import time

from app.repositories.ItemRepository import ItemRepository
from app.repositories.PlayerItemProgressRepository import PlayerItemProgressRepository
from app.repositories.PointRepository import PointRepository
from app.repositories.ResourceRepository import ResourceRepository
from app.repositories.UserItemRepository import UserItemRepository
from app.config.config import logger, asyncRedis
from app.services.maps import check_range
from app.utils.Json import format_error_response
from app.utils.User import is_overload


async def resource_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'get_resource': get_resource,
        'start_mine': start_mine,
        'check_mine': check_mine
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def fetch_resource_data(resource_id: int, db, current_user):
    """Получение и проверка данных ресурса и точки."""
    pointRep = PointRepository(db)
    point = await pointRep.get_point_by_id(resource_id)
    if not point or point['type'] != 'resources':
        return None, "Такого объекта не существует"

    if not check_range(point['lon'], point['lat'], current_user):
        return None, "Подойдите ближе для взаимодействия"

    if await is_overload(db, current_user):
        return None, "У вас перегруз. Избавьтесь от лишних предметов"

    resource = await ResourceRepository(db).get_resource_by_id(point['object_id'])
    if not resource:
        return None, "Такого объекта не существует"

    return {
        'point': point,
        'resource': resource
    }, None


async def calculate_harvest_time(resource_type: str, resource_harvest_time_seconds, db, current_user):
    tier_tool = await ResourceRepository(db).get_tier_tool(resource_type, current_user['id'])
    logger.debug(f"tier_tool: {tier_tool}")
    # если нет предмета для добычи, то скорость добычи в два раза медленнее
    if not tier_tool:
        harvest_time_seconds = resource_harvest_time_seconds * 2
    else:
        # если есть, то скорость зависит от уровня предмета, чем выше уровень, тем быстрее
        tier_tool = tier_tool.get('tier', 1)
        harvest_time_seconds = round(resource_harvest_time_seconds / tier_tool)
    return harvest_time_seconds


async def get_resource(body, db, current_user):
    resource_id = int(body['resource_id'].split("p")[1])
    if not resource_id:
        return format_error_response("Такого объекта не существует")
    logger.debug(f"resource_id: {resource_id}")
    resource_data, error_message = await fetch_resource_data(resource_id, db, current_user)
    logger.debug(f"resource_data: {resource_data}")
    if error_message:
        return format_error_response(error_message)

    resource = resource_data['resource']
    harvest_time_seconds = await calculate_harvest_time(resource['type'], resource['harvest_time_seconds'], db, current_user)

    return {
        "success": True,
        "data": {
            'name': resource['name'],
            'description': resource['description'],
            'harvest_time_seconds': harvest_time_seconds
        },
        "message": None,
        "successMessage": None
    }


async def start_mine(body, db, current_user):
    resource_id = int(body['resource_id'].split("p")[1])
    if not resource_id:
        return format_error_response("Такого объекта не существует")

    resource_data, error_message = await fetch_resource_data(resource_id, db, current_user)
    if error_message:
        return format_error_response(error_message)

    cache_key = f"point.used:{resource_id}"
    cache_key_user = f"point.used:{resource_id}:user.id:{current_user['id']}"
    already_mine = await asyncRedis.get(cache_key)
    logger.debug(f"already_mine={already_mine}")
    if already_mine:
        return format_error_response("Объект пока недоступен")
    resource = resource_data['resource']
    harvest_time_seconds = await calculate_harvest_time(resource['type'], resource['harvest_time_seconds'], db, current_user)
    logger.debug(f"harvest_time_seconds: {harvest_time_seconds}")
    # запишем в редис, что кто-то начал добывать этот ресурс, пока не выйдет таймаут - его нельзя добывать
    # таймаут: время добычи + кулдаун
    cache_ttl = resource['cooldown_seconds'] + harvest_time_seconds
    await asyncRedis.setex(cache_key, cache_ttl, 1)
    # и сохраним таймаут на получение награды, чтобы нельзя было получить раньше, чем прошло время добычи
    # и привязываем к пользователю таймаут для получения награды, чтобы никто другой ее не получил
    await asyncRedis.setex(cache_key_user, cache_ttl, (time.time() + harvest_time_seconds))
    return {
        "success": True,
        "data": {'mine': True},
        "message": None,
        "successMessage": None
    }


async def check_mine(body, db, current_user):
    resource_id = int(body['resource_id'].split("p")[1])
    if not resource_id:
        return format_error_response("Такого объекта не существует")

    resource_data, error_message = await fetch_resource_data(resource_id, db, current_user)
    if error_message:
        return format_error_response(error_message)

    cache_key_user = f"point.used:{resource_id}:user.id:{current_user['id']}"
    access_get_reward = await asyncRedis.get(cache_key_user)
    cur_time = time.time()
    logger.debug(f"access_get_reward={access_get_reward}")
    logger.debug(f"cur_time={cur_time}")
    if not access_get_reward or float(access_get_reward) > cur_time:
        return format_error_response("Объект пока недоступен")

    async with db.transaction():
        user_item_rep = UserItemRepository(db)
        reward = []
        resource = resource_data['resource']
        loot = json.loads(resource['loot'])
        logger.debug(f"loot={loot}")
        item_ids = [item['item_id'] for item in loot]
        loot_data_map = {item['item_id']: item for item in loot}
        logger.debug(f"loot_data_map={loot_data_map}")
        items = await ItemRepository(db).get_items_by_id(item_ids)
        for item in items:
            reward.append({
                'name': item['name'],
                'quantity': loot_data_map[item['id']]['quantity'],
            })
            # и добавим предметы пользователю
            await user_item_rep.add_item(current_user['id'], item['id'], loot_data_map[item['id']]['quantity'])
        logger.debug(f"reward={reward}")
        await asyncRedis.delete(cache_key_user)
        # обновим опыт использования инструментов
        experience = 3  # todo тут можно подумать над прогрессивной шкалой
        await PlayerItemProgressRepository(db).update_progress(current_user['id'], 'tool',
                                                               experience, resource['type'])

    return {
        "success": True,
        "data": {
            'reward': reward
        },
        "message": None,
        "successMessage": None
    }
