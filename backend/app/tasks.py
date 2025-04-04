from celery.schedules import crontab

from app.config.config import logger, DATABASE_URL
from celery import Celery
import psycopg2

from app.config.config import redis
from app.repositories.QuestRepository import QuestRepository

appCelery = Celery(
    'tasks',
    broker="redis://redis:6379/0",  # Укажи правильный адрес Redis
    backend="redis://redis:6379/0"
)

appCelery.autodiscover_tasks(['app.tasks'])  # Автоматическое обнаружение задач

# Настройки Celery (опционально)
appCelery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        'cleanup-coordinates-twice-a-day': {
            'task': 'cleanup_expired_coordinates',
            'schedule': crontab(hour='0,12', minute='0'),  # Выполнение в 00:00 и 12:00
        },
        'cleanup_repeatable_quest-twice-a-day': {
            'task': 'cleanup_repeatable_quest',
            'schedule': crontab(hour='0', minute='0'),
        },
    },
)


@appCelery.task(name='cleanup_expired_coordinates')
def cleanup_expired_coordinates():
    logger.debug('Выполняется фоновая задача cleanup_expired_coordinates')
    all_players = redis.zrange("player_locations", 0, -1)
    for player_id in all_players:
        if not redis.exists(f"player_last_seen:{player_id}"):
            # Удаляем из GeoSet
            redis.zrem("player_locations", player_id)
    # и тут же проверим и очистим устаревшие сообщения чата
    all_message = redis.zrange("chat:global:messages:locations", 0, -1)
    for message_id in all_message:
        if not redis.exists(f"chat:global:message:{message_id}"):
            redis.zrem("chat:global:messages:locations", message_id)


@appCelery.task(name='cleanup_repeatable_quest')
def cleanup_repeatable_quest():
    logger.debug('Запуск очистки повторяемых квестов')
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as curs:
            # Получаем ID всех повторяемых квестов
            curs.execute('SELECT id FROM quests WHERE is_repeatable = true')
            repeatable_quest_ids = [row[0] for row in curs.fetchall()]
            logger.debug(f'Найдено повторяемых квестов: {len(repeatable_quest_ids)}')
            # Удаляем связанные записи в цикле
            for quest_id in repeatable_quest_ids:
                # Удаление из таблицы user_quests (пример)
                curs.execute(
                    "DELETE FROM user_quests WHERE quest_id = %s",
                    (quest_id,)
                )
                logger.debug(f'Удалены записи для квеста {quest_id}')
            conn.commit()
            logger.debug('Все операции удаления завершены')

    except Exception as e:
        conn.rollback()
        logger.error(f'Ошибка при очистке квестов: {str(e)}')
        raise

    finally:
        conn.close()


@appCelery.task
def save_coords_to_db(player_id, long, lat):
    logger.debug('Выполняется фоновая задача save_coords_to_db')
    conn = psycopg2.connect(DATABASE_URL)
    with conn.cursor() as curs:
        # Преобразуем координаты в формат WKT (POINT)
        point = f'POINT({long} {lat})'
        curs.execute(
            """
            INSERT INTO player_coordinates_history (user_id, coordinates, timestamp)
            VALUES (%s, ST_GeogFromText(%s), NOW())
            """,
            (player_id, point)
        )
        conn.commit()
    conn.close()
