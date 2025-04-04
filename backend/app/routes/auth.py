from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from pydantic import BaseModel
from passlib.context import CryptContext

from app.repositories.UserProfileRepository import UserProfileRepository
from app.repositories.UserQuestRepository import UserQuestRepository
from app.repositories.UserRepository import UserRepository
from app.config.database import get_db
from app.services.jwt import create_access_token, create_refresh_token
from app.services.users import get_current_user
from app.config.config import JWT_EXPIRATION, SECRET_KEY, JWT_ALGORITHM, JWT_REFRESH_EXPIRATION

# Создаем роутер
router = APIRouter(
    prefix="/api/auth",  # Префикс для всех маршрутов
    tags=["Auth"]  # Тег для документации
)

# Шифрование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Пример модели данных
class LoginData(BaseModel):
    username: str
    password: str


# Авторизация
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    query = "SELECT * FROM users WHERE email = $1"
    user = await db.fetchrow(query, form_data.username)
    if not user or not pwd_context.verify(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # Создание access и refresh токенов
    access_token_expires = timedelta(minutes=JWT_EXPIRATION)
    access_token = create_access_token(data={"sub": str(user["id"])}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(days=JWT_REFRESH_EXPIRATION)
    refresh_token = create_refresh_token(data={"sub": str(user["id"])}, expires_delta=refresh_token_expires)

    # Сохраняем refresh токен в базе данных
    session_query = """
    INSERT INTO sessions (user_id, token, refresh_token, expires_at) 
    VALUES ($1, $2, $3, $4)
    """
    expires_at = datetime.utcnow() + access_token_expires
    await db.execute(session_query, user["id"], access_token, refresh_token, expires_at)

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# Модель для регистрации
class RegisterModel(BaseModel):
    username: str
    email: str
    password: str


# Регистрация
@router.post("/register")
async def register(user: RegisterModel, db=Depends(get_db)):
    existing_user = await UserRepository(db).get_user_by_email(user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = pwd_context.hash(user.password)
    async with db.transaction():
        user_id = await UserRepository(db).add_user(user.username, user.email, hashed_password)
        if not user_id:
            raise HTTPException(status_code=400, detail="Registration failed")

        await UserProfileRepository(db).create_profile(user_id['id']) # создадим профиль
        await UserQuestRepository(db).add_user_quest(user_id['id'], 1) # назначим первый квест
    return {"id": user_id, "message": "User registered successfully"}


# Защищённый маршрут
@router.get("/protected")
async def protected_route(current_user=Depends(get_current_user)):
    return {"message": f"Hello, {current_user['username']}!"}


# Эндпоинт для обновления access токена с использованием refresh токена
class RefreshToken(BaseModel):
    refresh_token: str
@router.post("/refresh")
async def refresh_access_token(refresh_token: RefreshToken, db=Depends(get_db)):
    # Декодируем refresh токен
    payload = jwt.decode(refresh_token.refresh_token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    # Проверяем, есть ли этот refresh токен в базе данных
    query = "SELECT * FROM sessions WHERE user_id = $1 AND refresh_token = $2"
    session = await db.fetchrow(query, int(user_id), str(refresh_token.refresh_token))
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Генерация нового access токена
    new_access_token = create_access_token(data={"sub": user_id})

    # Опционально обновляем дату истечения access токена в базе данных
    new_expires_at = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION)
    await db.execute("UPDATE sessions SET token = $3, expires_at = $1 WHERE user_id = $2", new_expires_at, int(user_id),
                     new_access_token)

    return {"access_token": new_access_token, "token_type": "bearer"}
