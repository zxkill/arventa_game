import json
import time
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

from app.config.database import get_db
from app.controllers.avatar import avatar_action
from app.controllers.chat import chat_action
from app.controllers.feedback import feedback_action
from app.controllers.mail import mail_action
from app.controllers.map import get_regions
from app.controllers.market import market_action
from app.controllers.point import point_action
from app.controllers.portal import portal_action
from app.controllers.profile import profile_action
from app.controllers.quest import quest_action
from app.controllers.recipe import recipe_action
from app.controllers.resource import resource_action
from app.controllers.settings import settings_action
from app.controllers.webpush import webpush_action
from app.services.users import get_current_user
from app.routes import auth
from app.config.config import logger
from app.controllers.player import player_action

from app.websocket import manager
from app.controllers.monster import monster_action

logger.info('Старт проекта')

# Инициализация FastAPI
app = FastAPI()

# Подключаем маршруты
app.include_router(auth.router)

# Настройки CORS
origins = ["https://bitrix.zxkill.ru", "https://xn--80aafm4bpr.xn--p1ai"]  # Укажите конкретные домены для безопасности
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

test_client = TestClient(app)


# WebSocket эндпоинт
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str, db=Depends(get_db)):
    start_time = time.time()
    try:
        # Проверяем токен и извлекаем user_id
        current_user = await get_current_user(token, db)
        user_id = current_user['id']

        logger.debug(f"Websocket user_id={user_id}")
        # Подключаем пользователя
        await manager.connect(websocket, user_id)

        try:
            while True:
                # Получаем сообщение от клиента
                data = await websocket.receive_text()
                request = json.loads(data)
                request_id = request.get("id")
                endpoint = request.get("endpoint")
                logger.debug(f"endpoint: {endpoint}")
                # Логируем время начала запроса
                logger.debug(f"Request received at {time.time() - start_time} seconds")

                body = request.get("body", {})
                logger.debug(f"request={request}")

                # Сопоставление endpoints с функциями
                endpoint_actions = {
                    "/player": player_action,
                    "/quest": quest_action,
                    "/map/getRegions": get_regions,
                    "/settings": settings_action,
                    "/monster": monster_action,
                    "/resource": resource_action,
                    "/recipe": recipe_action,
                    "/points": point_action,
                    "/feedback": feedback_action,
                    "/chat": chat_action,
                    "/profile": profile_action,
                    "/avatar": avatar_action,
                    "/webpush": webpush_action,
                    "/portal": portal_action,
                    "/mail": mail_action,
                    "/market": market_action,
                }
                # Получаем соответствующую функцию
                action = endpoint_actions.get(endpoint)

                # Если функция найдена, выполняем её
                if action:
                    try:
                        result = await action(body, db, current_user)
                        # Формируем успешный ответ
                        response = {"id": request_id, "success": True, "data": result}
                    except Exception as e:
                        logger.error(f"Error handling {endpoint}: {e}")
                        response = {"id": request_id, "success": False, "error": str(e)}
                else:
                    # Если endpoint неизвестен
                    response = {"id": request_id, "success": False, "error": "Unknown endpoint"}

                # Логируем время окончания запроса
                logger.debug(f"Response sent at {time.time() - start_time} seconds")
                logger.debug(f"response={response}")
                if websocket.application_state == WebSocketState.CONNECTED:
                    # Отправляем ответ обратно клиенту
                    await manager.send_personal_message(response, user_id)
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket.application_state == WebSocketState.CONNECTED:
            await websocket.send_text(json.dumps({"message": f"WebSocket error: {e}"}))
