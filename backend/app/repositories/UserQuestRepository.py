import json
from datetime import datetime
from typing import Optional

from asyncpg.connection import Connection

from app.repositories.QuestRepository import QuestRepository
from app.config.config import logger


class UserQuestRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def get_user_quest_by_id(self, user_id: int, quest_id: int) -> Optional[dict]:
        query = "SELECT quest_id, status, progress FROM user_quests WHERE user_id = $1 AND quest_id = $2"
        return await self.conn.fetchrow(query, user_id, quest_id)

    async def is_quest_already_use(self, user_id: int, quest_id: int) -> bool:
        query = "SELECT 1 FROM user_quests WHERE user_id = $1 AND quest_id = $2"
        return bool(await self.conn.fetchrow(query, user_id, quest_id))

    async def add_user_quest(self, user_id: int, quest_id: int) -> bool:
        quest = await QuestRepository(self.conn).get_quest_by_id(quest_id)
        progress = []
        status = 'completed'
        completed_at = datetime.now()
        for cond in json.loads(quest["conditions"]):
            current = 0
            target = {}  # Инициализируем пустой словарь для target
            # Общая логика для всех действий
            if cond["action"] == "collect":
                status = 'in_progress'
                completed_at = None
                if "target_id" in cond:  # Добавляем target_id, если он есть
                    target["target_id"] = cond["target_id"]
            elif cond["action"] == "say":
                current = 1
                if "target_id" in cond:
                    target["target_id"] = cond["target_id"]
            elif cond["action"] == "kill":
                status = 'in_progress'
                completed_at = None
                if "target_id" in cond:
                    target["target_id"] = cond["target_id"]
            elif cond["action"] == "craft":
                status = 'in_progress'
                completed_at = None
                if "target_id" in cond:
                    target["target_id"] = cond["target_id"]
            elif cond["action"] == "close_portal":
                status = 'in_progress'
                completed_at = None
                if "target_id" in cond:
                    target["target_id"] = cond["target_id"]
            elif cond["action"] == "all_actions":
                status = 'in_progress'
                completed_at = None
            progress.append({
                "current": current,
                "required": int(cond["quantity"]),
                "action": cond["action"],
                **target  # Распаковываем target, даже если он пустой
            })

        query = """
        INSERT INTO user_quests (user_id, quest_id, status, progress, started_at, completed_at)
        VALUES ($1, $2, $4, $3, NOW(), $5)
        """

        result = await self.conn.execute(query, user_id, quest_id, json.dumps(progress), status, completed_at)
        return result.endswith("1")

    async def get_quest_in_progress_by_user_id(self, user_id: int) -> list:
        statuses = ['in_progress', 'completed']
        query = "SELECT quest_id FROM user_quests WHERE user_id = $1 AND status = ANY($2)"
        return await self.conn.fetch(query, user_id, statuses)

    async def delete_user_quest(self, user_id: int, quest_id: int) -> bool:
        query = "DELETE FROM user_quests WHERE user_id = $1 AND quest_id = $2"
        result = await self.conn.execute(query, user_id, quest_id)
        return result.endswith("1")

    async def update_status_user_quest(self, user_id: int, quest_id: int) -> bool:
        query = "UPDATE user_quests SET status = 'finished' WHERE user_id = $1 AND quest_id = $2"
        result = await self.conn.execute(query, user_id, quest_id)
        return result.endswith("1")
