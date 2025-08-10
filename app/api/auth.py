"""
app/api/auth.py
Реализует функции для регистрации и аутентификации пользователей с использованием JWT.
"""
import logging
import uuid

from fastapi import APIRouter, HTTPException, Depends, Response, Cookie, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from passlib.context import CryptContext

from app.api.dependencies import get_current_user
from app.models.models import User as UserModel, RefreshToken, User
from app.core.database import get_db
from app.services.user_service import get_user
from app.schemas.user_schemas import UserCreate, UserResponse, UserUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Извлечение конфигурационных данных
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_MINUTES = settings.refresh_token_expire_minutes


def create_access_token(to_encode: dict):
    """Функция для создания JWT токена"""

    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expires_at})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def create_refresh_token(user: UserModel, db: AsyncSession):
    """
    Создает и сохраняет refresh token в базе данных, удаляя предыдущие от того же пользователя.
    После авторизации с одного устройства, сессия с другого устройства пропадает.
    """
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))

    expires_at = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    token = str(uuid.uuid4())
    refresh_token = RefreshToken(user_id=user.id, token=token, expires_at=expires_at)
    db.add(refresh_token)
    await db.commit()

    return str(token)


async def verify_refresh_token(db: AsyncSession, refresh_token: str) -> RefreshToken | None:
    """
    Верифицирует refresh token: проверяет, существует ли он, не истек ли срок действия.
    """
    query = select(RefreshToken).where(RefreshToken.token == refresh_token)
    result = await db.execute(query)
    refresh_token_record = result.scalars().first()

    if not refresh_token_record:
        return None

    if refresh_token_record.expires_at < datetime.utcnow():
        await db.delete(refresh_token_record)
        await db.commit()
        return None

    return refresh_token_record


@router.post("/registration/", status_code=status.HTTP_201_CREATED,
             response_model=UserResponse, summary="Создание пользователя")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация пользователя"""
    try:
        async with db.begin():
            existing_user = await get_user(db, user.username)
            if existing_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Пользователь с таким никнеймом уже зарегистирирован")

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
    except Exception as e:
        logger.exception(f"Ошибка при регистрации пользователя: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка регистрации пользователя")


@router.post("/login/")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db),
                response: Response = Response()):
    """Аутентификация и получение JWT токена"""
    try:
        user = await get_user(db, form_data.username)
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль.")

        access_token = create_access_token({"sub":user.username})
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=True
        )

        refresh_token = await create_refresh_token(user, db)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=True
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.exception(f"Ошибка при входе пользователя: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка авторизации")


@router.get("/me", response_model=UserResponse, summary="Получение информации текущего пользователя")
async def read_current_user(current_user: UserModel = Depends(get_current_user)):
    """Возвращает информацию о текущем пользователе."""
    return current_user


@router.put("/me", response_model=UserResponse, summary="Обновление информации пользователя")
async def update_user_info(user_update: UserUpdate, current_user: UserModel = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """Обновляет информацию текущего пользователя"""
    try:
        async with db.begin():
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
        logger.exception(f"Ошибка при обновлении информации пользователя: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка обновления информации пользователя")


@router.get("/get_tokens")
async def get_tokens(access_token: str = Cookie(None), refresh_token: str = Cookie(None)):
    return {"access_token":access_token, "refresh_token":refresh_token}


@router.post("/refresh/")
async def refresh_token_endpoint(refresh_token: str = Cookie(None), db: AsyncSession = Depends(get_db),
                                 response: Response = Response()):
    """Обновление access token с использованием refresh token"""
    try:
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is missing")

        refresh_token_record = await verify_refresh_token(db, refresh_token)
        if not refresh_token_record:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        user_id = refresh_token_record.user_id  # Получаем пользователя из refresh token
        user = await db.scalar(select(User).where(User.id == user_id))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        access_token = create_access_token({"sub":user.username, "user_id": user.id})

        new_refresh_token = await create_refresh_token(user, db)

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=True,
        )

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=True,
        )

        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.exception(f"Ошибка при обновлении токена: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка обновления токена")
