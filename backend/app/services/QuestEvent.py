import json
from app.config.config import logger
from app.websocket import manager


class QuestEvent:
    def __init__(self, action: str, target_id: int, quantity: int, user_id: int):
        self.action = action
        self.target_id = target_id
        self.quantity = quantity
        self.user_id = user_id


async def handle_event(game_event: QuestEvent, db):
    logger.debug(f"Game Event: {game_event.action}")
    logger.debug(f"Game Event: {game_event.target_id}")
    # Получить активные квесты пользователя
    user_quests = await db.fetch("""
        SELECT uq.quest_id, uq.progress, q.conditions, q.name
        FROM user_quests uq
        JOIN quests q ON uq.quest_id = q.id
        WHERE uq.user_id = $1 AND uq.status = 'in_progress'
    """, game_event.user_id)

    logger.debug(f"Event: user_quests: {user_quests}")

    for quest in user_quests:
        progress = json.loads(quest["progress"])  # Десериализуем строку JSON в объект
        conditions = json.loads(quest["conditions"])  # Десериализуем строку JSON в объект

        progress_updated = False  # Флаг для отслеживания изменений прогресса

        # Обновление прогресса
        for condition, progress_item in zip(conditions, progress):
            logger.debug(f"Event: condition: {condition}")
            logger.debug(f"Event: progress_item: {progress_item}")

            if (
                    (condition["action"] == game_event.action or condition["action"] == 'all_actions')
                    and ('target_id' not in condition or condition['target_id'] == game_event.target_id)
            ):
                if progress_item["current"] < condition["quantity"]:
                    progress_item["current"] += game_event.quantity
                    if progress_item["current"] > condition["quantity"]:
                        progress_item["current"] = condition["quantity"]
                    progress_updated = True

        if progress_updated:
            logger.debug(f"Updated Progress: {progress}")

            # Проверка выполнения квеста
            if all(p["current"] >= c["quantity"] for c, p in zip(conditions, progress)):
                # Завершение квеста
                await db.execute("""
                    UPDATE user_quests SET progress = $1, status = 'completed', completed_at = NOW()
                    WHERE user_id = $2 AND quest_id = $3
                """, json.dumps(progress), game_event.user_id, quest["quest_id"])

                await manager.send_personal_message({
                    "success": True,
                    "data": None,
                    "action": "update_quests",
                    "successMessage": f"Квест '{quest['name']}' завершен!",
                    "message": None
                }, game_event.user_id)
            else:
                # Обновление прогресса квеста
                await db.execute("""
                    UPDATE user_quests SET progress = $1
                    WHERE user_id = $2 AND quest_id = $3
                """, json.dumps(progress), game_event.user_id, quest["quest_id"])

                await manager.send_personal_message({
                    "success": True,
                    "data": None,
                    "action": "update_quests",
                    "successMessage": f"Прогресс квеста '{quest['name']}' обновлен!",
                    "message": None
                }, game_event.user_id)
        else:
            logger.debug("No progress update needed.")


"""
Возможные экшены для целей квеста
say - поговорить с кем-то
kill - убить монстров
collect - собрать предметы
close_portal - закрытие портала

"""
# event = QuestEvent(action="kill", target_id=101, quantity=1, user_id=42)
# await handle_event(event, db)
