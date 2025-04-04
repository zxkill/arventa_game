import json

from app.config.config import redis
from typing import Optional, Union


class Cache:
    def __init__(self):
        self.redis = redis

    def save_to_cache(self, key: str, value: Union[dict, list]):
        # Сериализуем в JSON и сохраняем в Redis
        if value is not None:  # Проверяем, что значение передано
            self.redis.set(key, json.dumps(value))
        else:
            print(f"Ошибка: нет данных для сохранения в кэш по ключу {key}")

    def get_from_cache(self, key: str) -> Optional[Union[dict, list]]:
        data = self.redis.get(key)
        if data:
            return json.loads(data)  # Десериализуем данные из JSON
        return None

    def clear_cache_by_prefix_key(self, prefix: str):
        cursor = 0
        while True:
            cursor, keys = self.redis.scan(cursor, match=f"{prefix}*")
            if keys:
                self.redis.delete(*keys)  # Удаляем найденные ключи
            if cursor == 0:
                break
