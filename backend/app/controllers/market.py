import json

from app.repositories.MailRepository import MailRepository
from app.repositories.MarketListingRepository import MarketListingRepository
from app.repositories.UserRepository import UserRepository
from app.services.item import ItemHelper
from app.services.text import text_to_html
from app.services.webpush import send_notification
from app.utils.Item import item_type_name
from app.utils.Json import format_error_response, serialize_datetimes
from app.websocket import manager
from app.config.config import logger


async def market_action(body, db, current_user):
    action = body['action']
    actions_map = {
        'get_lots': get_lots,
        'buy': buy,
        'create_lot': create_lot
    }
    action_func = actions_map.get(action)
    if action_func:
        return await action_func(body, db, current_user)
    return format_error_response('Неверное действие')


async def get_lots(body, db, current_user):
    page = 1
    per_page = 30
    lot_records = await MarketListingRepository(db).get_lots(page, per_page)
    logger.debug(f"lot_records {lot_records}")
    lots = []
    item_helper = ItemHelper(db, current_user)
    for lot in lot_records:
        item_data = {
            'id': lot['item_db_id'],
            'item_id': lot['item_db_id'],
            'name': lot['name'],
            'description': lot['description'],
            'tier': lot['tier'],
            'type': lot['type'],
            'item_type': item_type_name(lot['type']),
            'damage': lot['damage'],
            'armor': lot['armor'],
            'resource_type': lot['resource_type'],
            'weight': lot['weight'],
            'is_stackable': lot['is_stackable'],
            'is_equippetable': lot['is_equippetable'],
            'body_part': lot['body_part'],
            'effect': item_helper.item_effects_mapped(lot['effect']),
        }
        lots.append({
            'id': lot['lot_id'],
            'expires_at': lot['expires_at'].strftime('%Y-%m-%d %H:%M:%SZ'),
            'item_data': item_data,
            'price': lot['price'],
            'quantity': lot['lot_quantity'],
        })
    return {
        "success": True,
        "data": lots,
        "message": None,
        "successMessage": None
    }


# todo
async def buy(body, db, current_user):
    lot_id = int(body.get("lot_id"))
    if not lot_id:
        return format_error_response("Идентификатор лота не передан.")

    try:
        async with db.transaction():
            # Блокируем выбранный лот для предотвращения параллельных покупок
            lot = await db.fetchrow(
                """
                SELECT *
                FROM market_listings
                WHERE id = $1
                FOR UPDATE
                """,
                lot_id
            )
            if not lot:
                return format_error_response("Лот не найден.")

            if lot["status"] != "active":
                return format_error_response("Лот больше не доступен.")

            if lot["seller_id"] == current_user["id"]:
                return format_error_response("Нельзя покупать свой собственный лот.")

            # Рассчитываем общую стоимость покупки
            total_cost = lot["price"] * lot["quantity"]

            # Блокируем строку покупателя для безопасного обновления баланса
            buyer = await db.fetchrow(
                "SELECT id, silver FROM users WHERE id = $1 FOR UPDATE",
                current_user["id"]
            )
            if buyer is None:
                return format_error_response("Покупатель не найден.")
            if buyer["silver"] < total_cost:
                return format_error_response("Недостаточно средств для покупки.")

            # Блокируем строку продавца для обновления его баланса
            seller = await db.fetchrow(
                "SELECT id, silver FROM users WHERE id = $1 FOR UPDATE",
                lot["seller_id"]
            )
            if seller is None:
                return format_error_response("Продавец не найден.")

            # Обновляем баланс: списываем у покупателя и начисляем продавцу
            await db.execute(
                "UPDATE users SET silver = silver - $1 WHERE id = $2",
                total_cost, buyer["id"]
            )
            await db.execute(
                "UPDATE users SET silver = silver + $1 WHERE id = $2",
                total_cost, seller["id"]
            )

            # Передаём предмет: обновляем владельца в таблице user_items
            await db.execute(
                "UPDATE user_items SET user_id = $1 WHERE id = $2",
                buyer["id"], lot["user_item_id"]
            )

            # Помечаем лот как завершённый
            await db.execute(
                "UPDATE market_listings SET status = 'completed' WHERE id = $1",
                lot_id
            )

            # Записываем транзакцию в историю
            await db.execute(
                """
                INSERT INTO market_transactions 
                    (buyer_id, seller_id, market_listing_id, user_item_id, price, quantity)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                buyer["id"],
                seller["id"],
                lot_id,
                lot["user_item_id"],
                lot["price"],
                lot["quantity"]
            )
        # Если транзакция завершилась успешно
        return {
            "success": True,
            "data": {"buy": True},
            "message": None,
            "successMessage": "Покупка успешно завершена."
        }
    except Exception as e:
        # Логирование ошибки (можно заменить на реальное логирование)
        logger.exception("Ошибка при покупке:", e)
        return format_error_response("Ошибка при обработке запроса на покупку.")


async def create_lot(body, db, current_user):
    """
    Создаёт лот на продажу.

    Ожидаемые параметры в body:
      - item_id: идентификатор записи в таблице user_items (предмет из инвентаря),
      - price: цена продажи (число, > 0),
      - quantity: количество предметов для лота (число, > 0).

    Возвращает JSON-подобный словарь с ключами: success, message, data.
    """
    # Валидация входных параметров
    try:
        item_id = int(body.get("item_id"))
        price = int(body.get("price"))
        quantity = int(body.get("quantity"))
    except (TypeError, ValueError):
        return format_error_response("Некорректные входные данные.")

    if price <= 0 or quantity <= 0:
        return format_error_response("Цена и количество должны быть положительными.")

    try:
        async with db.transaction():
            # Получаем запись предмета из инвентаря игрока с блокировкой для изменения
            inventory_item = await db.fetchrow(
                """
                SELECT *
                FROM user_items
                WHERE id = $1 AND user_id = $2 AND is_equipped = false
                FOR UPDATE
                """,
                item_id, current_user["id"]
            )
            if not inventory_item:
                return format_error_response("Предмет не найден в вашем инвентаре или он надет.")

            available_quantity = inventory_item["quantity"]
            if available_quantity < quantity:
                return format_error_response("Недостаточно предметов для продажи.")

            # Подготавливаем данные о предмете для лота. Сохраним копию данных (например, как JSON),
            # при этом переопределим количество на продаваемое.
            item_data = dict(inventory_item)
            item_data = serialize_datetimes(item_data)
            item_data["quantity"] = quantity

            if available_quantity == quantity:
                # Если продаётся весь объект, полностью удаляем его из инвентаря.
                await db.execute(
                    """
                    DELETE FROM user_items
                    WHERE id = $1
                    """,
                    inventory_item["id"]
                )
            else:
                # Если предмет стекаемый и продаётся не всё, уменьшаем количество.
                await db.execute(
                    """
                    UPDATE user_items
                    SET quantity = quantity - $1
                    WHERE id = $2
                    """,
                    quantity, inventory_item["id"]
                )

            # Создание лота с датой истечения через 30 дней.
            # Предполагается, что таблица market_listings имеет поле item_data типа JSONB.
            listing = await db.fetchrow(
                """
                INSERT INTO market_listings 
                    (seller_id, item_data, listing_type, price, quantity, status, created_at, expires_at)
                VALUES ($1, $2, 'sell', $3, $4, 'active', now(), now() + interval '30 days')
                RETURNING id
                """,
                current_user["id"], json.dumps(item_data), price, quantity
            )

            return {
                "success": True,
                "data": {"lot_id": listing["id"]},
                "message": None,
                "successMessage": "Лот успешно создан."
            }
    except Exception as e:
        logger.exception("Ошибка при создании лота:", e)
        return format_error_response("Ошибка при создании лота.")
