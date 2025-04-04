import json
from typing import Optional
from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class MonsterRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_monster_by_ids(self, monster_ids: list) -> Optional[list]:
        self.cache.clear_cache_by_prefix_key('monsters:')
        cache_key = f"monsters:{','.join(map(str, monster_ids))}"
        monsters_data = self.cache.get_from_cache(cache_key)
        if monsters_data:
            return monsters_data
        query = """
                SELECT
                    *
                FROM monsters
                WHERE
                    id = ANY($1)
            """
        monsters_data = await self.conn.fetch(query, monster_ids)
        monsters_data_dict = [dict(monster) for monster in monsters_data]
        self.cache.save_to_cache(cache_key, monsters_data_dict)

        return monsters_data_dict

    async def get_monster_by_id(self, monster_id: int) -> Optional[dict]:
        self.cache.clear_cache_by_prefix_key('monster:')
        cache_key = f"monster:{monster_id}"
        monster_data = self.cache.get_from_cache(cache_key)
        if monster_data:
            logger.debug(f"monster_data_dict={monster_data}")
            return monster_data
        query = """
                SELECT
                    *
                FROM monsters
                WHERE
                    id = $1
            """
        monster_data = await self.conn.fetchrow(query, monster_id)
        monster_data_dict = dict(monster_data)
        logger.debug(f"monster_data_dict={monster_data_dict}")
        self.cache.save_to_cache(cache_key, monster_data_dict)
        return monster_data_dict
