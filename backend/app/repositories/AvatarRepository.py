import json

from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class AvatarRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_avatar_for_user(self, user_id: int) -> list:
        # todo получим список доступных аватаров пользователю и потом получим этот список
        query = "SELECT id, title, description, url FROM avatars"
        return await self.conn.fetch(query)
