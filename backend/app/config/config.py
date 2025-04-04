import os

from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from loguru import logger
from redis import Redis, from_url
from redis.asyncio import Redis as AsyncRedis, from_url as async_from_url

# import sys

# Загрузка переменных из файла .env
load_dotenv()

# Получение переменных
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "60"))
JWT_REFRESH_EXPIRATION = int(os.getenv("JWT_REFRESH_EXPIRATION", "30"))
# Радиус поиска (в метрах)
SEARCH_RADIUS = os.getenv("SEARCH_RADIUS", "200")
PLAYER_COORDS_TTL = os.getenv("PLAYER_COORDS_TTL", "15")
# начальный радиус возможного взаимодейтсвия игрока с объектами, в метрах
DEFAULT_INTERACTION_PLAYER_RADIUS = os.getenv("DEFAULT_INTERACTION_PLAYER_RADIUS", 60)

VAPID_PUBLIC_KEY = "BBECmT60vswiNni3amDUVUQpgQiq7Sd5a-yqJf_Ues9q8mNy8SGlX7oyHD8vDjNRKqhwV8tMXVJWMrhmThKuqzQ"
VAPID_PRIVATE_KEY = "4vkj6O5O-WivUhrmaLtpni1AOAUoE3Sm3No3PC9Ul_8"
VAPID_CLAIMS = {
    "sub": "mailto:zxkill@gmail.com"
}

# Удаление стандартного логирования
logger.remove()

# Логирование в консоль
# logger.add(sys.stdout, level="DEBUG", format="{time} {level} {message}")

# Логирование в файл (с ротацией и сжатием)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="1 day",  # Ротация: 1 День
    retention="1 month",  # Хранить логи 1 месяц
    compression="zip",  # Сжимать архивы
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Подключение к Redis
redis: Redis = from_url("redis://redis:6379/0", decode_responses=True)
asyncRedis: AsyncRedis = async_from_url("redis://redis:6379/0", decode_responses=True)

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
