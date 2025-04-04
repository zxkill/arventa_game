from app.config.config import logger, asyncRedis

ALLOW_ACTIONS_EVENT = [
    'say',
    'kill',
    'collect',
    'close_portal',
    'craft'
]

class ActionsEvent:
    def __init__(self, action: str, user_id: int):
        self.action = action
        self.user_id = user_id
        self.cache_id_day = f"actions.events.day:{user_id}"


    async def handle_event(self):
        logger.debug(f"Actions Event: {self.action}")
        logger.debug(f"Actions Event: {self.user_id}")

        if self.action in ALLOW_ACTIONS_EVENT:
            if await asyncRedis.exists(self.cache_id_day):
                await asyncRedis.set(self.cache_id_day, int(await asyncRedis.get(self.cache_id_day)) + 1)
            else:
                await asyncRedis.set(self.cache_id_day, 1)
        else:
            logger.error(f" Такой тип действий не поддерживается Actions Event: {self.action}")

"""
Возможные экшены
say - поговорить с кем-то
kill - убить монстров
collect - собрать предметы
close_portal - закрытие портала
craft - создание предметов
"""

