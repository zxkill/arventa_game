import json
import uuid
from datetime import datetime, timedelta

import pytz
from starlette.websockets import WebSocketState

from fastapi import WebSocket as websocket
from app.config.config import logger, asyncRedis
from app.services.users import get_player_coords
from app.services.webpush import send_notification
from app.utils.Json import format_error_response
from app.websocket import manager

RADIUS_SEARCH_MESSAGE = 1000  # игрокам в каком радиусе доступны сообщения, в метрах


async def chat_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'send': send,
        'get_messages': get_messages
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def send(body, db, current_user):
    message = body.get('message')

    if message:
        # Генерируем уникальный ID для сообщения
        message_id = str(uuid.uuid4())

        # Получаем координаты игрока
        player_coords = get_player_coords(current_user)
        lon, lat = player_coords

        # Формируем строку сообщения
        utc_time = datetime.now(pytz.utc)
        timestamp = utc_time.strftime('%Y-%m-%d %H:%M:%SZ')
        user_id = current_user['id']
        user_name = current_user['username']
        message_to_save = f"{timestamp}|{user_id}|{user_name}|{message}"

        # Сохраняем координаты сообщения в Redis GEO
        await asyncRedis.geoadd("chat:global:messages:locations", (lon, lat, message_id))

        # Сохраняем само сообщение с его ID
        await asyncRedis.set(f"chat:global:message:{message_id}", message_to_save, ex=86400)

        # Ищем nearby игроков
        nearby_players = await asyncRedis.georadius(
            "players:locations", float(lon), float(lat), RADIUS_SEARCH_MESSAGE, unit="m", withdist=False, withcoord=True
        )

        # Формируем данные сообщения для отправки
        message_data = {
            "timestamp": timestamp,
            "user_id": user_id,
            "user_name": user_name,
            "message": message
        }

        # Отправляем сообщение по вебсокету nearby игрокам
        for player in nearby_players:
            player_id = player[0]
            logger.debug(f"Отправили сообщение: {player_id}")
            result = await get_messages(body, db, current_user)
            result['action'] = 'update_chat'
            await manager.send_personal_message(result, int(player_id))

        return {
            "success": True,
            "data": {'send': True},
            "message": None,
            "successMessage": None
        }

    return {
        "success": False,
        "data": {'send': False},
        "message": "Ошибка: сообщение пустое",
        "successMessage": None
    }


async def get_messages(body, db, current_user):
    # Получаем текущие координаты игрока
    player_coords = get_player_coords(current_user)
    if player_coords is None:
        return {
            "success": False,
            "data": {"messages": []},
            "message": None,
            "successMessage": None
        }
    lon, lat = player_coords

    # Ищем сообщения в радиусе 1 км
    nearby_message_ids = await asyncRedis.georadius(
        "chat:global:messages:locations",
        lon,
        lat,
        RADIUS_SEARCH_MESSAGE,
        unit="m"
    )

    if nearby_message_ids is None or len(nearby_message_ids) == 0:
        return {
            "success": False,
            "data": {"messages": []},
            "message": None,
            "successMessage": None
        }

    # Получаем текущее время и время 24 часа назад
    now = datetime.now()
    time_limit = now - timedelta(hours=24)

    # Получаем текст сообщений по их ID и фильтруем по времени
    messages = []
    logger.debug(f"nearby_message_ids {nearby_message_ids}")
    for message_id in nearby_message_ids:
        message = await asyncRedis.get(f"chat:global:message:{message_id}")
        if message:
            # message_text = message.decode()
            timestamp_str, user_id, user_name, message_content = message.split('|', 3)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%SZ')

            # Фильтруем сообщения по времени
            if timestamp >= time_limit:
                messages.append({
                    "timestamp": timestamp_str,
                    "user_id": user_id,
                    "user_name": user_name,
                    "message": message_content
                })

    if messages is None or len(messages) == 0:
        return {
            "success": False,
            "data": {"messages": []},
            "message": None,
            "successMessage": None
        }
    logger.debug(f"messages111 {messages}")
    # Сортируем сообщения по дате
    messages.sort(key=lambda x: x['timestamp'])

    # Ограничиваем количество сообщений до 100
    messages = messages[:100]

    return {
        "success": True,
        "data": {"messages": messages},
        "message": None,
        "successMessage": None
    }
