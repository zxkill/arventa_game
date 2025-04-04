from typing import Optional

from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class RecipeRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_recipes(self) -> Optional[list]:
        query = "SELECT id, item_id, materials_required, crafting_time, quantity_crafting_item FROM crafting_recipes"
        return await self.conn.fetch(query)

    async def get_recipe(self, recipe_id: int) -> Optional[dict]:
        query = "SELECT id, item_id, materials_required, crafting_time, quantity_crafting_item FROM crafting_recipes WHERE id = $1"
        return await self.conn.fetchrow(query, recipe_id)