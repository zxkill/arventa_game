import random
from app.config.config import logger
from app.repositories.PlayerItemProgressRepository import PlayerItemProgressRepository

ITEM_TYPE_MAPPING = {
    'tool': 'Инструмент',
    'weapon': 'Оружие',
    'armor': 'Броня',
    'resource': 'Ресурс'
}

# данные о получаемом предмете и данные обо всех предметах игрока
async def check_item_drops(item, items_data, db, current_user, knife_tier=None):
    drop_rate = item['drop_rate'] # шанс выпадения указанный у предмета
    logger.debug("Checking item drops")

    # если это шкуря зверя, то проверим наличие ножа в инвентаре
    if item['id'] == 3:
        for item_data in items_data:
            if item_data['type'] == 'tool' and item_data['resource_type'] == 'skin':
                if not knife_tier or knife_tier < item_data['tier']:
                    knife_tier = item_data['tier']
        if knife_tier:
            # обновим опыт использования инструментов
            experience = 3  # todo тут можно подумать над прогрессивной шкалой
            await PlayerItemProgressRepository(db).update_progress(current_user['id'], 'tool',
                                                                   experience, 'skin')
            # и зададим шанс выпадения в зависимости от уровня ножа
            drop_rate = 0.55 + (0.05 * knife_tier)

    logger.debug(f"drop_rate = {drop_rate}")
    rand = random.random()  # генерируем случайное число от 0 до 1
    return rand <= drop_rate  # если выпало (rand <= drop_rate), возвращаем True

def item_type_name(item_type):
    return ITEM_TYPE_MAPPING[item_type]