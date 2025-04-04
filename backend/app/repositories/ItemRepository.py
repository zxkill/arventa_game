from typing import Optional

from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class ItemRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_items_by_id(self, item_ids: list) -> list:
        self.cache.clear_cache_by_prefix_key('items:')
        cache_key = f"items:{','.join(map(str, item_ids))}"
        items_data = self.cache.get_from_cache(cache_key)
        if items_data:
            return items_data
        query = "SELECT id, name, type, rarity, damage, armor, effect, resource_type, weight, price, is_stackable, description, is_equippetable, body_part, tier FROM items WHERE id = ANY($1)"
        items_data = await self.conn.fetch(query, item_ids)

        items_data_dict = [dict(item) for item in items_data]
        self.cache.save_to_cache(cache_key, items_data_dict)
        return items_data_dict

    async def is_equippetable(self, item_id: int) -> dict | list | bool:
        # self.cache.clear_cache_by_prefix_key('item:is:equippetable:')
        cache_key = f"item:is:equippetable:{item_id}"
        item_data = self.cache.get_from_cache(cache_key)
        if item_data:
            return item_data
        query = "SELECT 1 FROM items WHERE id = $1 AND is_equippetable=true"
        item_data = bool(await self.conn.fetch(query, item_id))
        self.cache.save_to_cache(cache_key, item_data)
        return item_data

    async def is_stackable(self, item_id: int) -> bool:
        # self.cache.clear_cache_by_prefix_key('item:is:stackable:')
        cache_key = f"item:is:stackable:{item_id}"
        item_data = self.cache.get_from_cache(cache_key)
        if item_data:
            return item_data
        query = "SELECT 1 FROM items WHERE id = $1 AND is_stackable=true"
        item_data = bool(await self.conn.fetch(query, item_id))
        self.cache.save_to_cache(cache_key, item_data)
        return item_data