import psycopg2
import json

# Подключение к базе данных
conn = psycopg2.connect('postgresql://user:password@db:5432/game_db')
cursor = conn.cursor()

# Укажите USER_ID или None для очистки всех пользователей
USER_ID = 1

# Список операций для очистки (SQL-запрос, условие WHERE)
operations = [
    ("UPDATE users SET silver = 0", "id"),
    ("DELETE FROM user_quests", "user_id"),
    ("DELETE FROM user_items", "user_id"),
    ("DELETE FROM portal_closures", "user_id"),
    ("DELETE FROM player_item_progress", "user_id"),
    ("DELETE FROM player_coordinates_history", "user_id"),
    ("DELETE FROM market_listings", "seller_id"),
    ("DELETE FROM market_transactions", "seller_id"),
    ("DELETE FROM mails", "recipient_id"),
    ("DELETE FROM feedback", "user_id"),
]

try:
    for query, condition in operations:
        if USER_ID is not None:
            # Добавляем условие для конкретного пользователя
            sql = f"{query} WHERE {condition} = %s"
            cursor.execute(sql, (USER_ID,))
        else:
            # Очищаем все записи
            cursor.execute(query)

    if USER_ID is not None:
        sql = f"INSERT INTO user_quests (user_id, quest_id, status, progress, started_at, completed_at) VALUES (%s, %s, %s, %s, NOW(), NOW())"
        cursor.execute(sql, (USER_ID, 1, 'completed', json.dumps([])))
    # Подтверждение изменений
    conn.commit()
    print("Данные успешно очищены!")

except Exception as e:
    # Откат при ошибке
    conn.rollback()
    print(f"Ошибка: {e}")

finally:
    # Закрытие подключения
    cursor.close()
    conn.close()
