from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from app.config.config import SECRET_KEY, JWT_ALGORITHM, oauth2_scheme, redis, DEFAULT_INTERACTION_PLAYER_RADIUS
from app.config.database import get_db


# Проверка JWT токена
async def get_current_user(token: str = Depends(oauth2_scheme), db=Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        query = "SELECT * FROM users WHERE id = $1"
        user = await db.fetchrow(query, int(user_id))
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# замена шаблонов текста
def replace_user_data(text: str, current_user):
    return text.replace("%username%", current_user['username'])


# Получаем координаты запрашивающего игрока
def get_player_coords(user):
    player_coords = redis.geopos("players:locations", user['id'])
    return player_coords[0]


def get_interaction_radius(user):
    return int(DEFAULT_INTERACTION_PLAYER_RADIUS * 1)
