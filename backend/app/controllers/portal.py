import json
import random
import time
import uuid

from app.repositories.ItemRepository import ItemRepository
from app.repositories.PlayerItemProgressRepository import PlayerItemProgressRepository
from app.repositories.PointRepository import PointRepository
from app.repositories.PortalClosuresRepository import PortalClosureRepository
from app.repositories.PortalRepository import PortalRepository
from app.repositories.ResourceRepository import ResourceRepository
from app.repositories.UserItemRepository import UserItemRepository
from app.config.config import logger, asyncRedis
from app.services.ActionsEvent import ActionsEvent
from app.services.QuestEvent import QuestEvent, handle_event
from app.services.maps import check_range
from app.services.text import text_to_html
from app.utils.Json import format_error_response
from app.utils.User import is_overload

DEFAULT_ENERGY_REQUIRED = 10

async def portal_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'get_portal': get_portal,
        'get_puzzle': get_puzzle,
        'check_puzzle': check_puzzle_and_portal_close,
        'get_stats': get_stats
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def fetch_portal_data(portal_id: int, db, current_user):
    """Получение и проверка данных ресурса и точки."""
    portal_id = int(portal_id)
    if not portal_id:
        return format_error_response("Такого объекта не существует")
    pointRep = PointRepository(db)
    point = await pointRep.get_point_by_id(portal_id)

    if not point or point['type'] != 'portals':
        return None, "Такого объекта не существует"

    if not check_range(point['lon'], point['lat'], current_user):
        return None, "Подойдите ближе для взаимодействия"

    if await is_overload(db, current_user):
        return None, "У вас перегруз. Избавьтесь от лишних предметов"

    portal = await PortalRepository(db).get_portal_by_ids([point['object_id']])
    portal = portal[0]
    portal['portal_id'] = portal['id']
    portal['id'] = point['id']  # хак, чтобы у монстров на карте были уникальные айди
    if not portal:
        return None, "Такого объекта не существует"
    return {
        'point': point,
        'portal': portal
    }, None


async def get_portal(body, db, current_user):
    portal_id = int(body['portal_id'].split("p")[1])
    if not portal_id:
        return format_error_response("Такого объекта не существует")
    logger.debug(f"portal_id: {portal_id}")

    portal_data, error_message = await fetch_portal_data(portal_id, db, current_user)
    logger.debug(f"portal_data: {portal_data}")
    if error_message:
        return format_error_response(error_message)

    return {
        "success": True,
        "data": {
            'name': portal_data['portal']['name'],
            'description': text_to_html(portal_data['portal']['description']),
            'energy_required': portal_data['portal']['tier'] * DEFAULT_ENERGY_REQUIRED,
        },
        "message": None,
        "successMessage": None
    }


async def get_puzzle(body, db, current_user):
    portal_id = int(body['portal_id'].split("p")[1])
    if not portal_id:
        return format_error_response("Такого объекта не существует")

    portal_data, error_message = await fetch_portal_data(portal_id, db, current_user)
    logger.debug(f"portal_data: {portal_data}")
    if error_message:
        return format_error_response(error_message)

    kit = ["☀", "✦", "❄", "⚡", "☂", "✈", "♠", "♥", "♦", "♣", "★", "☆", "⚔", "⚡", "☠", "⚙", "⚖", "⚜"]
    # Выбираем случайным образом 3 уникальных символа, которые будут целевой последовательностью
    # todo потом сделаем количество символов зависимым от уровня разлома
    sequence_symbols = random.sample(kit, 3)
    sequence = ''.join(sequence_symbols)

    # Формируем набор опций для выбора.
    # Пусть общее количество вариантов будет 6, из которых 3 обязательно должны совпадать с sequence_symbols.
    # Остальные 3 выбираем из оставшихся символов.
    remaining_symbols = [s for s in kit if s not in sequence_symbols]
    additional_options = random.sample(remaining_symbols, 3)
    options = sequence_symbols + additional_options

    # Перемешиваем опции, чтобы правильная последовательность не была на фиксированных позициях
    random.shuffle(options)

    # Генерируем уникальный идентификатор пазла
    puzzle_id = str(uuid.uuid4())

    await asyncRedis.hset('portal.puzzle.id:' + puzzle_id, mapping={'sequence': sequence, 'portal_id': portal_id, 'start_time': time.time()})
    await asyncRedis.expire('portal.puzzle.id:' + puzzle_id, 15)

    return {
        "success": True,
        "data": {
            "puzzle_id": puzzle_id,
            "sequence": sequence,
            "options": options,
        },
        "message": None,
        "successMessage": None
    }


async def check_puzzle_and_portal_close(body, db, current_user):
    puzzle_id = str(body.get('puzzle_id', ''))
    selected_sequence = str(body.get('selected_sequence', ''))
    if not puzzle_id or not selected_sequence:
        return format_error_response("Неверные входные данные")

    # Извлекаем сохранённую последовательность из Redis
    key = 'portal.puzzle.id:' + puzzle_id
    stored_sequence = await asyncRedis.hget(key, "sequence")
    if not stored_sequence:
        return format_error_response("Ошибка проверки последовательности")

    # Сравниваем последовательность, выбранную игроком, с сохранённой
    if selected_sequence == stored_sequence:
        async with db.transaction():
            portal_id = await asyncRedis.hget(key, "portal_id")
            start_time = await asyncRedis.hget(key, "start_time")
            # Вычисляем время закрытия на бэке
            closure_time = time.time() - float(start_time)

            portal_data, error_message = await fetch_portal_data(int(portal_id), db, current_user)

            # Если закрытие произведено быстрее 3 секунд, начисляется бонус.
            base_points = DEFAULT_ENERGY_REQUIRED * portal_data['portal']['tier']
            bonus = 0
            if closure_time < 3:
                bonus = int((3 - closure_time) * 1)
            points = base_points + bonus

            if error_message:
                return format_error_response(error_message)
            # 1. Забрать энергию арвенты
            user_items = await UserItemRepository(db).get_user_item_by_item_ids([5], current_user['id'])
            user_items = user_items[0] if user_items else None

            energy_used = portal_data['portal']['tier'] * DEFAULT_ENERGY_REQUIRED
            if user_items['quantity'] < energy_used:
                return {
                    "success": False,
                    "data": {
                        'closed': False
                    },
                    "message": 'У вас недостаточно Энергии Арвенты',
                    "successMessage": None
                }
            await UserItemRepository(db).destroy(user_items['id'], user_items['quantity'], energy_used)

            # 2. Начислить очки
            await PortalClosureRepository(db).add(current_user['id'], int(portal_id), True, points, closure_time, energy_used)
            # 3. Проставить для точки запрет на отображение на таймаут
            await asyncRedis.setex(f"point.used:{portal_id}", portal_data['portal']['cooldown_seconds'], 1)
            await asyncRedis.delete(key)

            # событие для отслеживания квестов
            event = QuestEvent(action='close_portal', target_id=portal_data['portal']['id'], quantity=1,
                               user_id=current_user['id'])
            await handle_event(event, db)

            await ActionsEvent(action='close_portal', user_id=current_user['id']).handle_event()

            return {
                "success": True,
                "data": {
                    'closed': True
                },
                "message": None,
                "successMessage": "Разлом закрыт."
            }
    else:
        # Если последовательности не совпадают, возвращаем сообщение об ошибке
        return format_error_response("Неверная последовательность. Разлом остаётся открытым.")


async def get_stats(body, db, current_user):
    rows = await PortalClosureRepository(db).get_stats()

    # Форматируем результаты
    leaderboard = []
    for i, row in enumerate(rows, start=1):
        leaderboard.append({
            "position": i,
            "user_id": row["user_id"],
            "username": row["username"] if row["username"] else f"User{row['user_id']}",
            "total_points": row["total_points"],
            "closures_count": row["successful_attempts"],
            "total_attempts": row["total_attempts"],
            #"success_rate": f"{row['success_rate']}%",
            "avg_closure_time": f"{round(row['avg_closure_time'], 2)} с" if row["avg_closure_time"] is not None else "N/A",
            "total_energy_used": row["total_energy_used"]
        })
    return {
        "success": True,
        "data": leaderboard,
        "message": None,
        "successMessage": None
    }