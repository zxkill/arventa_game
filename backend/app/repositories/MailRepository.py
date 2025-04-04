from typing import Optional
from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class MailRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_messages_by_user_id(self, user_id: int) -> Optional[list]:
        query = """
                SELECT
                    *
                FROM mails
                WHERE
                    recipient_id = $1
                ORDER BY created_at DESC
                LIMIT 30
            """

        return await self.conn.fetch(query, user_id)

    async def add_message(self, sender_id, recipient_id, subject, message) -> None:
        query = "INSERT INTO mails (sender_id, recipient_id, subject, message, created_at, is_read) VALUES ($1, $2, $3, $4, NOW(), False) RETURNING id"
        return await self.conn.fetchrow(query, sender_id, recipient_id, subject, message)


    async def check_allow_message(self, mail_id: int, recipient_id) -> Optional[list]:
        query = """
                SELECT
                    id
                FROM mails
                WHERE
                    id = $1 AND recipient_id = $2
            """

        return await self.conn.fetch(query, mail_id, recipient_id)

    async def read(self, mail_id: int) -> bool:
        query = "UPDATE mails SET is_read = True WHERE id = $1"
        result = await self.conn.execute(query, mail_id)
        return result.endswith("1")

    async def delete(self, mail_id: int) -> bool:
        query = "DELETE FROM mails WHERE id = $1"
        result = await self.conn.execute(query, mail_id)
        return result.endswith("1")
