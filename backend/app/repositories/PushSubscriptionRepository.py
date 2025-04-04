from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class PushSubscriptionRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_subscriptions_by_user(self, user_id: int) -> list:
        query = "SELECT user_id, endpoint, p256dh, auth FROM push_subscriptions WHERE user_id = $1;"
        return await self.conn.fetch(query, user_id)

    async def get_all_subscriptions(self) -> list:
        query = "SELECT user_id, endpoint, p256dh, auth FROM push_subscriptions;"
        return await self.conn.fetch(query)

    async def create_subscription(self, endpoint: str, p256dh: str, auth: str, user_id: int):
        query = "SELECT 1 FROM push_subscriptions WHERE endpoint = $1 AND auth = $2 AND user_id = $3;"
        endpoint_isset = bool(await self.conn.fetchrow(query, endpoint, auth, user_id))
        if not endpoint_isset:
            query = "INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth) VALUES ($1, $2, $3, $4)"
            result = await self.conn.execute(query, user_id, endpoint, p256dh, auth)
            if result.endswith("1"):
                return True
        return False

    async def delete_subscription(self, endpoint: str, user_id: int):
        query = "SELECT id FROM push_subscriptions WHERE endpoint = $1 and user_id = $2;"
        endpoint_isset = await self.conn.fetchrow(query, endpoint, user_id)
        if endpoint_isset:
            query = "DELETE FROM push_subscriptions WHERE id = $1;"
            result = await self.conn.execute(query, endpoint_isset['id'])
            if result.endswith("1"):
                return True
        return False