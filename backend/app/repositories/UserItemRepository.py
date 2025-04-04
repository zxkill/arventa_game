from asyncpg.connection import Connection

from app.repositories.ItemRepository import ItemRepository
from app.config.config import logger
from app.services.ActionsEvent import ActionsEvent
from app.services.QuestEvent import handle_event, QuestEvent


class UserItemRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    async def add_item(self, user_id: int, item_id: int, quantity: int, durability: int = 1000) -> bool:
        is_stackable = await ItemRepository(self.conn).is_stackable(item_id)
        if is_stackable and await self.is_item_user(user_id, item_id):
            # Если предмет можно складывать, увеличиваем количество и выбираем максимальную прочность
            query = """
                UPDATE user_items
                SET quantity = user_items.quantity + $3,
                    durability = GREATEST(user_items.durability, $4)
                WHERE user_id = $1 AND item_id = $2
            """
        else:
            query = "INSERT INTO user_items (user_id, item_id, quantity, durability) VALUES ($1, $2, $3, $4)"
        result = await self.conn.execute(query, user_id, item_id, quantity, durability)
        if result.endswith("1"):
            event = QuestEvent(action='collect', target_id=item_id, quantity=quantity, user_id=user_id)
            await handle_event(event, self.conn)
            await ActionsEvent(action='collect', user_id=user_id).handle_event()
            return True
        else:
            return False

    # уничтожаем предмет из инвентаря
    async def destroy(self, user_item_id: int, current_count: int, count: int) -> bool:
        if count < current_count:
            # обновляем количество
            query = "UPDATE user_items SET quantity = $1 WHERE id = $2"
            result = await self.conn.execute(query, (current_count - count), user_item_id)
        else:
            # удаляем строчку
            query = "DELETE FROM user_items WHERE id = $1"
            result = await self.conn.execute(query, user_item_id)
        if result.endswith("1"):
            return True
        else:
            return False

    async def get_items_by_user_id(self, user_id: list) -> list:
        query = "SELECT id, item_id, durability, modifications, quantity, is_equipped FROM user_items WHERE user_id = $1"
        return await self.conn.fetch(query, user_id)

    async def is_item_user(self, user_id: int, item_id: int) -> bool:
        query = "SELECT 1 FROM user_items WHERE user_id = $1 AND item_id = $2"
        return bool(await self.conn.fetchrow(query, user_id, item_id))

    async def equip(self, user_item_id: int, item_id: int, user_id: int) -> bool:
        async with self.conn.transaction():
            # Проверка текущего состояния предмета
            query = "SELECT is_equipped FROM user_items WHERE user_id = $1 AND id = $2"
            user_item_equipped = await self.conn.fetchrow(query, user_id, user_item_id)
            if user_item_equipped is None:
                logger.error(f"Item with id {user_item_id} not found for user {user_id}")
                return False

            is_equipped = not user_item_equipped["is_equipped"]
            # Получим часть тела для указанного предмета
            query = """
                SELECT items.body_part 
                FROM items 
                RIGHT JOIN user_items ON items.id = user_items.item_id 
                WHERE items.id = $1 
                LIMIT 1
            """
            body_part = await self.conn.fetchrow(query, item_id)
            if not body_part or 'body_part' not in body_part:
                logger.error(f"Body part not found for item_id={item_id}")
                return False

            # Получим ID экипированного предмета на эту часть тела, если есть
            query = """
                SELECT user_items.id
                FROM user_items
                LEFT JOIN items ON items.id = user_items.item_id
                WHERE user_id = $1
                  AND is_equipped = TRUE
                  AND items.body_part = $2
            """
            equipped_item = await self.conn.fetchrow(query, user_id, body_part['body_part'])
            if equipped_item:
                logger.debug(f"equipped_item['id'] = {equipped_item['id']}")
                query = "UPDATE user_items SET is_equipped = FALSE WHERE id = $1"
                result = await self.conn.execute(query, equipped_item['id'])
                if result != "UPDATE 1":
                    logger.error(f"Failed to unequip item: id={equipped_item['id']}")
                    return False

            query = "UPDATE user_items SET is_equipped = $3 WHERE user_id = $1 AND id = $2"
            result = await self.conn.execute(query, user_id, user_item_id, is_equipped)
            if result != "UPDATE 1":
                logger.error(f"Failed to update item: user_id={user_id}, user_item_id={user_item_id}")
                return False

            return True

    async def get_user_item_by_id(self, user_item_id: int, user_id: int) -> dict:
        query = "SELECT id, item_id, quantity FROM user_items WHERE id = $1 AND user_id = $2"
        return await self.conn.fetchrow(query, user_item_id, user_id)

    async def get_user_item_by_item_ids(self, item_ids: list, user_id: int) -> list:
        query = "SELECT id, item_id, quantity FROM user_items WHERE item_id = ANY($1) AND user_id = $2"
        return await self.conn.fetch(query, item_ids, user_id)
