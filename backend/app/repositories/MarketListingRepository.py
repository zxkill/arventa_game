from typing import Optional
from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class MarketListingRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_lots(self, page: int = 1, per_page: int = 30) -> Optional[list]:
        offset = (page - 1) * per_page
        query = """
            SELECT 
                ml.id AS lot_id,
                ml.seller_id,
                (ml.item_data ->> 'user_item_id')::int AS user_item_id,
                ml.listing_type,
                ml.price,
                ml.quantity AS lot_quantity,
                ml.status,
                ml.created_at,
                ml.expires_at,
                ui.item_id,
                i.id AS item_db_id,
                i.name,
                i.type,
                i.rarity,
                i.damage,
                i.armor,
                i.effect,
                i.resource_type,
                i.weight,
                i.price,
                i.is_stackable,
                i.description,
                i.is_equippetable,
                i.body_part,
                i.tier,
                ml.item_data AS item_data_json
            FROM market_listings ml
            LEFT JOIN user_items ui 
                ON (ml.item_data ->> 'user_item_id')::int = ui.id
            LEFT JOIN items i 
                ON i.id = COALESCE(ui.item_id, (ml.item_data ->> 'item_id')::int)
            WHERE ml.status = 'active'
            ORDER BY ml.created_at DESC
            LIMIT $1 OFFSET $2
        """
        return await self.conn.fetch(query, per_page, offset)
