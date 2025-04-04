import asyncpg
from contextlib import asynccontextmanager

from app.config.config import DATABASE_URL


# Пул соединений
class DBPool:
    def __init__(self):
        self._pool = None

    async def get_pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=10,
                max_size=20,
                max_queries=50000,  # Максимальное количество запросов на одно соединение
                max_inactive_connection_lifetime=120
            )
        return self._pool


# Инициализация глобального объекта для пула
db_pool = DBPool()


# Получение соединения из пула
async def get_db():
    pool = await db_pool.get_pool()  # Получаем пул
    conn = await pool.acquire()  # Получаем соединение из пула
    try:
        yield conn  # Возвращаем соединение в зависимости
    finally:
        await pool.release(conn)  # Обязательно освобождаем соединение

# Подключение к базе данных
# async def get_db():
#     conn = await asyncpg.connect(DATABASE_URL)
#     try:
#         yield conn
#     finally:
#         await conn.close()
