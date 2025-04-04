import json
from datetime import datetime

from asyncpg.connection import Connection
from app.config.config import logger
from app.utils.Cache import Cache


class UserProfileRepository:
    def __init__(self, conn: Connection):
        self.conn = conn
        self.cache = Cache()

    async def get_profile_by_user_id(self, user_id: int) -> dict:
        query = "SELECT * FROM user_profiles WHERE id = $1"
        return await self.conn.fetchrow(query, user_id)

    async def save_settings(self, user_id: int, settings: dict) -> bool:
        if not settings:
            return False
        settings_json = json.dumps(settings)
        query = "UPDATE user_profiles SET settings = $2::jsonb WHERE user_id = $1"
        result = await self.conn.execute(query, user_id, settings_json)
        if result != "UPDATE 1":
            return False
        return True

    async def get_settings(self, user_id: int) -> str:
        query = "SELECT settings FROM user_profiles WHERE user_id = $1"
        row = await self.conn.fetchrow(query, user_id)
        return row["settings"] if row else {}

    async def create_profile(self, user_id: int) -> bool:
        query = "INSERT INTO user_profiles (user_id, settings) VALUES ($1, $2::jsonb) ON CONFLICT (user_id) DO NOTHING"
        result = await self.conn.fetchrow(query, user_id)
        return result == "INSERT 0 1"

    async def get_profile(self, user_id: int) -> dict:
        query = "SELECT bio, name, avatar_id, birthday FROM user_profiles WHERE user_id = $1"
        row = await self.conn.fetchrow(query, user_id)
        profile = {
            'bio': row["bio"],
            'name': row["name"],
            'avatar_id': row["avatar_id"],
            'birthday': row["birthday"].strftime("%Y-%m-%d") if row["birthday"] else None,
        }
        logger.debug(row)
        if row['avatar_id'] is not None:
            # подгрузим реальные данные об аватаре
            query_avatar = "SELECT id, title, description, url FROM avatars WHERE id = $1"
            row_avatar = await self.conn.fetchrow(query_avatar, row['avatar_id'])
            profile['avatar'] = row_avatar['url'] if row_avatar else '/img/avatars/avatar.png'
        else:
            logger.debug(f'get_profile233')
            profile['avatar'] = '/img/avatars/avatar.png'
        return profile

    async def save_profile(self, user_id: int, profile: dict) -> bool:
        if not profile:
            return False
        # Преобразуем дату в объект datetime, если необходимо
        if 'birthday' in profile and profile['birthday']:
            profile['birthday'] = datetime.strptime(profile['birthday'], '%Y-%m-%d').date()
        else:
            profile['birthday'] = None
        query = "UPDATE user_profiles SET name = $2, bio = $3, birthday = $4, avatar_id = $5 WHERE user_id = $1"
        result = await self.conn.execute(query,
                                         user_id,
                                         profile["name"],
                                         profile["bio"],
                                         profile["birthday"],
                                         profile["avatar_id"]
                                         )
        if result != "UPDATE 1":
            return False
        return True
