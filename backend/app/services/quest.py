import json

from app.controllers import portal
from app.repositories.MonsterRepository import MonsterRepository
from app.repositories.PortalRepository import PortalRepository
from app.repositories.UserQuestRepository import UserQuestRepository
from app.config.config import logger

from app.repositories.ItemRepository import ItemRepository
from app.repositories.PointRepository import PointRepository
from app.services.item import ItemHelper

ACTION_QUEST_MAP = {'kill': 'Убить', 'collect': 'Собрать', 'say': 'Поговорить', 'craft': 'Создать', 'close_portal': 'Закрыть разлом', 'all_actions': 'Любое действие'}


# Добираем информацию о квесте. Преобразуем айди предметов и т.д. в наименования
async def enrich_quest_data(quest: dict, db, user, listing=False):
    # Собираем данные о предметах и монстрах для целей
    all_item_ids = []
    all_monster_ids = []
    all_portals_ids = []
    quest_complete = True

    reward_data = json.loads(quest['reward'])
    if reward_data.get('items', None):
        items = reward_data['items']
        for item in items:
            logger.debug(f"ИД предметов: {item['id']}")
            all_item_ids.append(item['id'])

    conditions = json.loads(quest['conditions']) if isinstance(quest['conditions'], str) else quest['conditions']
    if conditions:
        for condition in conditions:
            if condition['action'] == 'collect' and 'target_id' in condition:
                all_item_ids.append(condition['target_id'])
            elif condition['action'] == 'kill' and 'target_id' in condition:
                all_monster_ids.append(condition['target_id'])
            elif condition['action'] == 'say' and 'target_id' in condition:
                all_monster_ids.append(condition['target_id'])
            elif condition['action'] == 'craft' and 'target_id' in condition:
                all_item_ids.append(condition['target_id'])
            elif condition['action'] == 'close_portal' and 'target_id' in condition:
                all_portals_ids.append(condition['target_id'])

    # Получаем данные о предметах
    item_data_map = {}
    if all_item_ids:
        items_data = await ItemRepository(db).get_items_by_id(all_item_ids)
        item_data_map = {item['id']: item for item in items_data}
    logger.debug(f"item_data_map = {item_data_map}")
    # Получаем данные о монстрах
    monster_data_map = {}
    if all_monster_ids:
        monsters_data = await MonsterRepository(db).get_monster_by_ids(
            all_monster_ids)  # надо будет переделать на другую сущность
        monster_data_map = {monster['id']: monster for monster in monsters_data}
    # Получаем данные о разломах
    portals_data_map = {}
    if all_portals_ids:
        portals_data = await PortalRepository(db).get_portal_by_ids(all_portals_ids)
        portals_data_map = {port['id']: port for port in portals_data}


    # Разбираем награду
    #reward = json.loads(quest['reward']) if isinstance(quest['reward'], str) else quest['reward']

    # если передан параметр listing, значит это просмотр принятых квестов и запросим данные о процессе выполнения
    progress = []
    if listing:
        user_quest = await UserQuestRepository(db).get_user_quest_by_id(user['id'], quest['id'])
        logger.debug(f"User quest: {user_quest}")
        if user_quest is not None and user_quest['progress'] is not None:
            progress = json.loads(user_quest['progress'])
            logger.debug(f"User quest progress: {progress}")

    detailed_conditions = []
    if conditions:
        for condition in conditions:
            detailed_condition = {
                "action": ACTION_QUEST_MAP[condition["action"]],
                "quantity": condition["quantity"],
            }
            if condition["action"] == "collect" and "target_id" in condition:
                item = item_data_map.get(condition["target_id"], {"name": "Неизвестный предмет"})
                detailed_condition["target_name"] = item.get("name", "Неизвестный предмет")
            elif condition["action"] == "kill" and "target_id" in condition:
                monster = monster_data_map.get(condition["target_id"], {"name": "Неизвестный монстр"})
                logger.debug(f"Monster quest {monster}")
                if monster:
                    detailed_condition["target_name"] = monster.get("name", "Неизвестный монстр")
            elif condition["action"] == "say" and "target_id" in condition:
                monster = monster_data_map.get(condition["target_id"], {"name": "Неизвестный монстр"})
                logger.debug(monster)
                if monster:
                    try:
                        detailed_condition["target_name"] = monster.get("name", "Неизвестный монстр")
                    except json.JSONDecodeError as e:
                        logger.error(f"Ошибка декодирования JSON данных монстра: {e}")
                        detailed_condition["target_name"] = "Неизвестный монстр"
                else:
                    detailed_condition["target_name"] = monster.get("name", "Неизвестный монстр")
            elif condition["action"] == "craft" and "target_id" in condition:
                item = item_data_map.get(condition["target_id"], {"name": "Неизвестный предмет"})
                detailed_condition["target_name"] = item.get("name", "Неизвестный предмет")
            elif condition["action"] == "close_portal" and "target_id" in condition:
                port = portals_data_map.get(condition["target_id"], {"name": "Неизвестный предмет"})
                detailed_condition["target_name"] = port.get("name", "Неизвестный предмет")

            # Добавляем текущий прогресс
            if progress:
                for prog in progress:
                    if (
                            prog["action"] == condition["action"]
                            and prog.get("target_id") == condition.get("target_id")
                    ):
                        detailed_condition["current"] = prog["current"]
                        logger.debug(f"Progress: {prog}")
                        if prog["required"] > prog["current"]:
                            quest_complete = False
                        break

            detailed_conditions.append(detailed_condition)

    quest_data = dict(quest)
    quest_data['completed'] = quest_complete
    # Дополняем информацию о награде
    if reward_data.get('items', None):
        for item in reward_data['items']:
            item_id = item['id']

            # Проверяем, существует ли информация о предмете
            if item_id in item_data_map:
                # Преобразуем asyncpg.Record в словарь для возможности изменения
                item_data = dict(item_data_map[item_id])
                item_data['item_id'] = item_id

                # Обрабатываем эффекты предмета
                effects = item_data.get('effect')
                if effects:
                    item_helper = ItemHelper(db, user)
                    item_data['effect'] = item_helper.item_effects_mapped(effects)

                # Обновляем информацию о предмете в награде
                item.update(item_data)

                # Логируем для отладки
                logger.debug(f"Оригинальные эффекты: {effects}")
                # logger.debug(f"Преобразованные эффекты: {effects_mapped}")

    return [quest_data, reward_data, detailed_conditions]
