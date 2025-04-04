from typing import Optional

from asyncpg.connection import Connection
from app.config.config import logger

"""
Возможные экшены для целей квеста
say - поговорить с кем-то
kill - убить монстров
collect - собрать предметы
craft
close_portal
"""


class QuestRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_quest_by_id(self, quest_id: int) -> Optional[dict]:
        query = "SELECT * FROM quests WHERE id = $1"
        return await self.conn.fetchrow(query, quest_id)

    async def get_repeatable_quests(self, user_id: int) -> Optional[list]:
        query = """
            SELECT quests.id
            FROM quests
            LEFT JOIN user_quests ON quests.id = user_quests.quest_id AND user_quests.user_id = $1
            WHERE quests.is_repeatable = true
              AND user_quests.quest_id IS NULL
          """
        return await self.conn.fetch(query, user_id)

    async def get_quest_by_ids(self, quest_ids: list) -> Optional[list]:
        query = "SELECT * FROM quests WHERE id = ANY($1)"
        return await self.conn.fetch(query, quest_ids)

    # получаем один новый квест доступный для пользователя
    async def get_new_quest(self, quest_ids: list, completed_quests: list) -> Optional[dict]:
        query = "SELECT * FROM quests WHERE id = ANY($1) AND id != ALL($2) ORDER BY id LIMIT 1"
        return await self.conn.fetchrow(query, quest_ids, completed_quests)

    async def get_next_by_order(self, old_quest):
        query = "SELECT id FROM quests WHERE type = 'main' AND sort > $1 ORDER BY sort LIMIT 1"
        return await self.conn.fetchrow(query, old_quest['sort'])