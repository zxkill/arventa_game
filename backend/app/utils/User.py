from app.repositories.UserItemRepository import UserItemRepository
from app.services.Character import Character
from app.services.item import ItemHelper


async def get_items_data(db, current_user):
    user_items = await UserItemRepository(db).get_items_by_user_id(current_user['id'])
    items_data = []

    if user_items:
        # Составляем список ID предметов и создаем карту user_items
        item_helper = ItemHelper(db, current_user)
        items_data = await item_helper.collect_data_item(user_items)

    return items_data

async def is_overload(db, current_user):
    items_data = await get_items_data(db, current_user)
    user_helper = Character(current_user, items_data)
    if user_helper.get_cur_weight() >= user_helper.get_max_weight():
        return True
    return False
