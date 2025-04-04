from typing import Optional
from asyncpg.connection import Connection


class ResourceRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_resource_by_ids(self, resource_ids: list) -> Optional[list]:
        query = """
                SELECT
                    *
                FROM resources
                WHERE
                    id = ANY($1)
            """
        return await self.conn.fetch(query, resource_ids)

    async def get_resource_by_id(self, resource_id: int) -> Optional[dict]:
        query = """
                SELECT
                    *
                FROM resources
                WHERE
                    id = $1
            """
        return await self.conn.fetchrow(query, resource_id)

    # получим уровень предмета, который есть у игрока для добычи данного ресурса
    async def get_tier_tool(self, resource_type: str, user_id: int) -> Optional[dict]:
        query = """
                        select tier
                        from items
                        right join user_items on items.id = user_items.item_id
                        where items.resource_type = $1 AND items.type = 'tool' AND user_items.user_id = $2
                        limit 1;
                    """
        return await self.conn.fetchrow(query, resource_type, user_id)