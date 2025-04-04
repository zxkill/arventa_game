from http.client import HTTPException
from typing import Dict, List
from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.config.config import logger
import httpx


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            disconnected_connections = []
            for connection in self.active_connections[user_id]:
                if connection.application_state == WebSocketState.CONNECTED:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending message to user {user_id}: {e}")
                        disconnected_connections.append(connection)
                else:
                    disconnected_connections.append(connection)

            # Удаляем отключённые соединения
            for connection in disconnected_connections:
                self.active_connections[user_id].remove(connection)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            return True
        else:
            return False

    async def broadcast(self, message: dict):
        disconnected_connections = []
        for user_id, user_connections in list(self.active_connections.items()):
            for connection in user_connections:
                if connection.application_state == WebSocketState.CONNECTED:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to user {user_id}: {e}")
                        disconnected_connections.append((user_id, connection))
                else:
                    disconnected_connections.append((user_id, connection))

        # Удаляем отключённые соединения
        for user_id, connection in disconnected_connections:
            self.active_connections[user_id].remove(connection)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        # await manager.broadcast({"action": "update_quests", "message": "Новый квест доступен!"})


manager = ConnectionManager()


async def handle_http_request(request: dict, token: str):
    request_id = request.get("id")
    endpoint = request.get("endpoint")
    logger.debug(f"endpoint: {endpoint}")
    method = request.get("method")
    query_params = request.get("query_params", {})
    body = request.get("body", {})

    # Формируем заголовок с токеном
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(verify=False) as client:
            # Формируем HTTP запрос
            if method == "GET":
                response = await client.get(endpoint, params=query_params, headers=headers)
            elif method == "POST":
                response = await client.post(endpoint, json=body, headers=headers)
            elif method == "PUT":
                response = await client.put(endpoint, json=body, headers=headers)
            elif method == "PATCH":
                response = await client.patch(endpoint, json=body, headers=headers)
            elif method == "DELETE":
                response = await client.delete(endpoint, headers=headers)
            else:
                return {"id": request_id, "success": False, "error": f"Unsupported method: {method}"}

            # Возвращаем JSON-ответ
            return {"id": request_id, "success": True, "data": response.json()}

    except HTTPException as e:
        return {"id": request_id, "success": False, "error": str(e)}
