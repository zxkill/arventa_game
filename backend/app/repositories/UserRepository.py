from typing import Optional

from asyncpg.connection import Connection
from app.config.config import logger


class UserRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def update_silver(self, user_id: int, silver_reward: int) -> bool:
        query = "UPDATE users SET silver = silver + $1 WHERE id = $2"
        result = await self.conn.execute(query, silver_reward, user_id)
        return result.endswith("1")

    async def get_user_by_email(self, email: str) -> Optional[dict]:
        query = "SELECT * FROM users WHERE email = $1"
        return await self.conn.fetchrow(query, email)

    async def add_user(self, username: str, email: str, password: str) -> Optional[dict]:
        query = "INSERT INTO users (username, email, password_hash) VALUES ($1, $2, $3) RETURNING id"
        return await self.conn.fetchrow(query, username, email, password)

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        query = "SELECT * FROM users WHERE id = $1"
        return await self.conn.fetchrow(query, user_id)

    async def find_by_username(self, q: str) -> Optional[list]:
        query = """
            SELECT
            id, username
            FROM users
            WHERE username ILIKE $1 || '%'
            LIMIT 5;
        """
        return await self.conn.fetch(query, q)
