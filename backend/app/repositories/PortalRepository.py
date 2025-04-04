import json
from typing import Optional
from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class PortalRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_portal_by_ids(self, portal_ids: list) -> Optional[list]:
        self.cache.clear_cache_by_prefix_key('portals:')
        cache_key = f"portals:{','.join(map(str, portal_ids))}"
        portals_data = self.cache.get_from_cache(cache_key)
        if portals_data:
            return portals_data
        query = """
                SELECT
                    *
                FROM portals
                WHERE
                    id = ANY($1)
            """
        portals_data = await self.conn.fetch(query, portal_ids)
        portals_data_dict = [dict(portal) for portal in portals_data]
        self.cache.save_to_cache(cache_key, portals_data_dict)

        return portals_data_dict
