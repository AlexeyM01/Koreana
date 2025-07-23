"""
auth.py
Реализует функции для регистрации и аутентификации пользователей с использованием JWT.
"""

from fastapi import APIRouter, HTTPException, Depends, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from passlib.context import CryptContext
from starlette.responses import HTMLResponse
from models import User as UserModel
from database import get_db, get_user
from schemas import UserCreate, UserResponse, UserUpdate
from config import settings
from dependencies import get_current_user
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Извлечение конфигурационных данных
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(username: str):
    """Функция для создания JWT токена"""

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub":username}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Функция для проверки JWT токена и возвращает полезную нагрузку, если верный токен"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


@router.post("/registration/", response_model=UserResponse, summary="Создание пользователя")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация пользователя"""
    async with db.begin():
        existing_user = await get_user(db, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким никнеймом уже зарегистирирован")

        # Хэшируем пароль
        hashed_password = pwd_context.hash(user.password)
        new_user = UserModel(
            username=user.username,
            hashed_password=hashed_password,
            registered_at=datetime.utcnow(),
            email=user.email,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return UserResponse.from_orm(new_user)


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db),
                response: Response = Response()):
    """Аутентификация и получение JWT токена"""
    try:
        user = await get_user(db, form_data.username)
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль.")

        access_token = create_access_token(user.username)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=True
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка {e}")


@router.get("/me", response_model=UserResponse, summary="Получение информации текущего пользователя")
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """Возвращает информацию о текущем пользователе."""
    return current_user


@router.get("/secure-data")
async def read_secure_data(access_token: str = Cookie(None), current_user: UserModel = Depends(get_current_user)):
    """Извлекает защищенные данные, проверяя токен из cookie-файла."""
    return {"message": "Это безопасные данные.", "user": current_user.username}


@router.put("/me", response_model=UserResponse, summary="Обновление информации пользователя")
async def update_user_info(user_update: UserUpdate, current_user: UserModel = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """Обновляет информацию текущего пользователя"""
    async with db.begin():
        try:
            existing_user = await get_user(db, user_update.username)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(status_code=400, detail="Имя пользователя уже зарегистрировано")

            current_user.username = user_update.username
            current_user.hashed_password = pwd_context.hash(user_update.password)
            current_user.email = user_update.email
            current_user.additional_info = user_update.additional_info

            await db.commit()
            await db.refresh(current_user)
            return UserResponse.from_orm(current_user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Возникла ошибка {e}.")
