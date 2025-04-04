import json

from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class FeedbackRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def create_feedback(self, user_id: int, title: str, description: str) -> bool:
        query = "INSERT INTO feedback (user_id, title, description) VALUES ($1, $2, $3)"
        result = await self.conn.execute(query, user_id, title, description)
        if result.endswith("1"):
            return True
        else:
            return False
