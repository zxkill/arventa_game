import hashlib
import json
from itertools import groupby

from numpy.ma.core import less_equal

from app.config.config import logger, asyncRedis
from app.repositories.MonsterRepository import MonsterRepository
from app.repositories.PointRepository import PointRepository
from app.repositories.PortalRepository import PortalRepository
from app.repositories.ResourceRepository import ResourceRepository
from app.services.maps import calculate_distance

from app.utils.Json import format_error_response

CACHE_POINTS_TTL = 60


async def point_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'view': view_point_action
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def view_point_action(body, db, current_user):
    z = body['z']
    nw = body['nw']
    se = body['se']
    if int(z) < 17:
        return {
            "success": True,
            "data": None,
            "message": None,
            'successMessage': None,
        }
    try:
        lat1, lon1 = map(float, nw.split(','))
        lat2, lon2 = map(float, se.split(','))
        logger.debug(f"coordinates squad {lat1} {lon1} {lat2} {lon2}")
    except ValueError:
        raise ValueError("Неверный формат строки координат. Ожидается: 'lat,lon'")

    if calculate_distance(lat1, lon1, lat2, lon2) > 1000:
        return {
            "success": True,
            "data": None,
            "message": None,
            'successMessage': None,
        }
    # SQL-запрос с извлечением широты (ST_Y) и долготы (ST_X)
    points = await PointRepository(db).get_points_by_sector(lon1, lat1, lon2, lat2)
    logger.debug(f"points = {points}")
    new_points = []
    for point in points:
        if not await asyncRedis.exists(f"point.used:{point['id']}"):
            # создаем новый массив точек, исключив точки ожидающие респаун
            new_points.append(point)
    # Генерируем хэш с использованием MD5
    points_id = [point['id'] for point in new_points]
    cache_key = f"points.view:{hashlib.md5(str(json.dumps(points_id)).encode()).hexdigest()}"
    cached_data = await asyncRedis.get(cache_key)
    if cached_data:
        return {
            "success": True,
            "data": json.loads(cached_data),
            "message": None,
            'successMessage': None,
        }
    logger.debug(f"new_points = {new_points}")
    # Сортировка данных по типу, чтобы groupby работал корректно
    new_points_sorted = sorted(new_points, key=lambda x: x['type'])
    # Разделение данных по типам
    points_by_type = {k: list(v) for k, v in groupby(new_points_sorted, key=lambda x: x['type'])}
    monster_ids = [p['object_id'] for p in points_by_type.get('monsters', [])]
    resource_ids = [p['object_id'] for p in points_by_type.get('resources', [])]
    portals_ids = [p['object_id'] for p in points_by_type.get('portals', [])]
    logger.debug(f"points_by_type: {points_by_type}")
    logger.debug(f"monster_ids: {monster_ids}")
    logger.debug(f"resource_ids: {resource_ids}")
    logger.debug(f"portals_ids: {portals_ids}")
    # Получение данных объектов
    monsters = await MonsterRepository(db).get_monster_by_ids(monster_ids) if monster_ids else []
    resources = await ResourceRepository(db).get_resource_by_ids(resource_ids) if resource_ids else []
    portals = await PortalRepository(db).get_portal_by_ids(portals_ids) if portals_ids else []

    # Карты для сопоставления
    monster_map = {m['id']: m for m in monsters}
    resource_map = {r['id']: r for r in resources}
    portal_map = {r['id']: r for r in portals}
    logger.debug(f"monster map: {monster_map}")
    logger.debug(f"resource map: {resource_map}")
    # Формирование результата
    points_data = [
        {
            "id": point["id"],
            "name": (
                monster_map[point['object_id']].get('name', 'Unknown') if point['type'] == 'monsters' else
                resource_map[point['object_id']].get('name', 'Unknown') if point['type'] == 'resources' else
                portal_map[point['object_id']].get('name', 'Unknown') if point['type'] == 'portals' else
                'Unknown'
            ),
            "object_id": point['object_id'],
            "type": point["type"],
            "coordinates": {"lat": point["lat"], "lon": point["lon"]}
        }
        for point in new_points
        if (point['type'] == 'monsters' and point['object_id'] in monster_map) or
           (point['type'] == 'resources' and point['object_id'] in resource_map) or
           (point['type'] == 'portals' and point['object_id'] in portal_map)
    ]

    await asyncRedis.setex(cache_key, CACHE_POINTS_TTL, json.dumps(points_data))
    return {
        "success": True,
        "data": points_data,
        "message": None,
        "successMessage": None
    }
