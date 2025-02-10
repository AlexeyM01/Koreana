"""
auth.py
Реализует функции для регистрации и аутентификации пользователей с использованием JWT.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from starlette.responses import HTMLResponse

from cache import set_token_in_cache
from models import User as UserModel
from database import get_db, get_user
from schemas import UserCreate, UserResponse, UserUpdate
from config import settings
from dependencies import get_current_user

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def create_access_token(data: dict, expires_delta: timedelta = None):
    """Создает JWT токен"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.get("/me", response_model=UserResponse, summary="Получение информации текущего пользователя")
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """Возвращает информацию о текущем пользователе"""
    return current_user


@router.post("/registration/", response_model=UserResponse, summary="Создание пользователя")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация пользователя"""
    try:
        async with db.begin():
            existing_user = await get_user(db, user.username)
            if existing_user:
                return HTMLResponse(status_code=400, content="Username already registered")
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
            return UserResponse.from_orm(new_user)
    except Exception as e:
        return HTMLResponse(status_code=200, content=f"Error {e} occurred")


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Аутентификация и получение JWT токена"""
    user = await get_user(db, form_data.username)
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    await set_token_in_cache(user.username, access_token, ACCESS_TOKEN_EXPIRE_MINUTES)
    return {"access_token": access_token, "token_type": "bearer"}


@router.put("/me", response_model=UserResponse, summary="Обновление информации пользователя")
async def update_user_info(user_update: UserUpdate, current_user: UserModel = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """Обновляет информацию текущего пользователя"""
    async with db.begin():
        try:
            existing_user = await get_user(db, user_update.username)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(status_code=400, detail="Username already registered")

            hashed_password = pwd_context.hash(user_update.password)
            current_user.username = user_update.username
            current_user.hashed_password = hashed_password
            current_user.email = user_update.email
            current_user.additional_info = user_update.additional_info

            db.add(current_user)
            await db.commit()
        except Exception as e:
            return HTMLResponse(status_code=200, content=f"Error {e} occurred")

    return UserResponse.from_orm(current_user)
