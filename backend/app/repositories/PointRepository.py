from typing import Optional
from asyncpg.connection import Connection
from app.config.config import logger

from app.utils.Cache import Cache


class PointRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_point_by_id(self, point_id: int) -> Optional[dict]:
        # self.cache.clear_cache_by_prefix_key('point:')
        cache_key = f"point:{point_id}"
        point_data = self.cache.get_from_cache(cache_key)
        if point_data:
            return point_data
        query = """
                SELECT
                    id,
                    type,
                    object_id,
                    ST_Y(coordinates::geometry) AS lon, 
                    ST_X(coordinates::geometry) AS lat
                FROM points
                WHERE
                    id = $1
            """
        point_data = await self.conn.fetchrow(query, point_id)
        point_data_dict = dict(point_data)
        self.cache.save_to_cache(cache_key, point_data_dict)
        return point_data_dict

    async def get_point_by_ids(self, point_id: list) -> Optional[list]:
        self.cache.clear_cache_by_prefix_key('points:')
        cache_key = f"points:{','.join(map(str, point_id))}"
        point_data = self.cache.get_from_cache(cache_key)
        if point_data:
            return point_data
        query = """
                SELECT
                    id,
                    type,
                    object_id,
                    ST_Y(coordinates::geometry) AS lon, 
                    ST_X(coordinates::geometry) AS lat
                FROM points
                WHERE
                    id = ANY($1)
            """
        point_data = await self.conn.fetch(query, point_id)
        point_data_dict = [dict(monster) for monster in point_data]
        self.cache.save_to_cache(cache_key, point_data_dict)
        return point_data_dict

    async def get_points_by_sector(self, lon1, lat1, lon2, lat2) -> Optional[list]:
        query = """
            SELECT 
                id, 
                type,
                object_id,
                ST_Y(coordinates::geometry) AS lat, 
                ST_X(coordinates::geometry) AS lon
            FROM points
            WHERE ST_Intersects(
                coordinates,
                ST_MakeEnvelope($1, $2, $3, $4, 4326)::geography
            )
        """
        # Извлекаем точки из базы данных
        return await self.conn.fetch(query, lon1, lat1, lon2, lat2)
