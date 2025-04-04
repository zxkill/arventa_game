import json

from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class ItemExperienceRequirementsRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_all(self) -> list:
        query = "SELECT level, experience_required FROM item_experience_requirements"
        return await self.conn.fetch(query)
