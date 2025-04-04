import json

from fastapi import Depends

from app.repositories.ItemRepository import ItemRepository
from app.config.config import logger
from app.config.database import get_db
from app.services.text import text_to_html
from app.services.users import get_current_user


class ItemHelper:
    def __init__(self, db: Depends(get_db), current_user=Depends(get_current_user)):
        self.db = db
        self.current_user = current_user

    ITEM_EFFECTS_MAP = {
        'endurance': 'Выносливость',
        'intelligence': 'Интеллект',
        'damage': 'Урон',
        'defense': 'Защита',
        'strength': 'Сила',
        'dexterity': 'Ловкость',
        'luck': 'Удача',
        'max_weight': 'Вес'
    }

    async def collect_data_item(self, user_items):
        items_data = []
        user_items_map = {user_item['id']: user_item for user_item in user_items}
        item_tmp = {user_item['id']: user_item['item_id'] for user_item in user_items}
        item_ids = list(item_tmp.values())
        logger.debug(f"item_ids = {item_ids}")
        logger.debug(f"item_tmp = {item_tmp}")
        if item_ids:
            # Получение данных о предметах
            items = await ItemRepository(self.db).get_items_by_id(item_ids)
            items_map = {item['id']: item for item in items}

            # Совмещение данных из user_items и items
            for user_item_id, user_item in user_items_map.items():
                effects_mapped = None
                item_data = items_map.get(item_tmp[user_item_id], {})
                logger.debug(f"item_data {item_data}")
                # Обрабатываем эффекты предмета

                effects = item_data.get('effect', '')
                logger.debug(f"effects {effects}")
                if effects is not '' and effects is not None:
                    logger.debug(f"effects {effects}")
                    effects_mapped = self.item_effects_mapped(effects)
                    logger.debug(f"effects_mapped {effects_mapped}")
                combined_item = {
                    "item_id": item_data['id'],
                    "user_item_id": user_item.get("id", None),
                    "quantity": user_item.get("quantity", 1),
                    "is_equipped": user_item.get("is_equipped", False),
                    "is_equippetable": item_data.get("is_equippetable", False),
                    "is_stackable": item_data.get("is_stackable", False),
                    "modifications": user_item.get("modifications", {}),
                    "name": item_data.get("name", "Неизвестный предмет"),
                    'weight': item_data.get("weight", 0),
                    'tier': item_data.get("tier", None),
                    'type': item_data.get("type", None),
                    'resource_type': item_data.get("resource_type", None),
                    'damage': item_data.get("damage", None),
                    'armor': item_data.get("armor", None),
                    'body_part': item_data.get("body_part", None),
                    "description": text_to_html(item_data.get("description", "")),
                    "effect": effects_mapped,
                    "effect_original": effects,
                }
                if item_data['type'] != 'resource':
                    combined_item['durability'] = user_item.get("durability", 1000),
                items_data.append(combined_item)
        return items_data

    def item_effects_mapped(self, effect: str):
        # Обрабатываем эффекты предмета
        effects = effect
        if effects:
            # Преобразуем строку в JSON, если это необходимо
            if isinstance(effects, str):
                try:
                    effects = json.loads(effects)
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка обработки эффекта предмета: {e}")
                    effects = {}

            # Заменяем ключи эффектов на значения из ITEM_EFFECTS_MAP
            return {self.ITEM_EFFECTS_MAP.get(key, key): value for key, value in effects.items()}
