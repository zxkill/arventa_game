from typing import Optional
from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class PortalClosureRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def add(self, user_id, portal_id, success, points, closure_time, energy_used) -> Optional[list]:
        query = """
                INSERT INTO portal_closures (
                    user_id, portal_id, success, points, closure_time,
                    energy_used, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                RETURNING id;
            """
        return await self.conn.fetchrow(
            query,
            user_id,
            portal_id,
            success,
            points,
            closure_time,
            energy_used
        )

    async def get_stats(self) -> Optional[list]:
        query = """
                SELECT 
                    pc.user_id,
                    u.username,
                    SUM(pc.points) AS total_points,
                    COUNT(*) AS total_attempts,
                    COUNT(*) FILTER (WHERE pc.success = true) AS successful_attempts,
                    CASE 
                        WHEN COUNT(*) = 0 THEN 0
                        ELSE ROUND(100.0 * COUNT(*) FILTER (WHERE pc.success = true) / COUNT(*), 2)
                    END AS success_rate,
                    AVG(pc.closure_time) FILTER (WHERE pc.success = true) AS avg_closure_time,
                    SUM(pc.energy_used) AS total_energy_used
                FROM portal_closures pc
                LEFT JOIN users u ON pc.user_id = u.id
                GROUP BY pc.user_id, u.username
                ORDER BY total_points DESC
                LIMIT 50;
            """

        return await self.conn.fetch(query)