import json

from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class PlayerItemProgressRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def update_progress(self, user_id: int, item_type: str, experience_gained: int,
                              resource_type: str = None) -> bool:
        logger.debug(f"PlayerItemProgressRepository: {user_id}, {item_type}, {experience_gained}, {resource_type}")
        check_query = """
        SELECT current_experience, current_level FROM player_item_progress
        WHERE user_id = $1 AND type_item = $2 AND type_resource = $3;
        """
        progress = await self.conn.fetchrow(check_query, user_id, item_type, resource_type)

        if progress is None:
            insert_query = """
            INSERT INTO player_item_progress (user_id, type_item, type_resource, current_experience, current_level)
            VALUES ($1, $2, $3, $4, 1)
            RETURNING current_experience, current_level;
            """
            progress = await self.conn.fetchrow(insert_query, user_id, item_type, resource_type, experience_gained)
        else:
            update_query = """
            UPDATE player_item_progress
            SET current_experience = current_experience + $4
            WHERE user_id = $1 AND type_item = $2 AND type_resource = $3
            RETURNING current_experience, current_level;
            """
            progress = await self.conn.fetchrow(update_query, user_id, item_type, resource_type, experience_gained)

        next_level_query = """
        SELECT experience_required FROM item_experience_requirements
        WHERE level = $1;
        """
        next_level_experience = await self.conn.fetchrow(next_level_query, progress["current_level"] + 1)

        if next_level_experience and progress["current_experience"] >= next_level_experience["experience_required"]:
            level_up_query = """
            UPDATE player_item_progress
            SET current_level = current_level + 1
            WHERE user_id = $1 AND type_item = $2 AND type_resource = $3;
            """
            bool(await self.conn.execute(level_up_query, user_id, item_type, resource_type))

        return False

    async def get_current_level_for_item(self, user_id: int, item_type: str, resource_type: str) -> dict:
        query = """
            SELECT current_level FROM player_item_progress WHERE user_id = $1 AND type_item = $2 AND type_resource = $3;
        """
        return await self.conn.fetchrow(query, user_id, item_type, resource_type)

    async def get_current_progress(self, user_id: int) -> list:
        query = """
            SELECT p.type_item, p.type_resource, p.current_experience, r.experience_required, p.current_level
            FROM player_item_progress p
            JOIN item_experience_requirements r
            ON p.current_level + 1 = r.level
            WHERE p.user_id = $1;
        """
        return await self.conn.fetch(query, user_id)