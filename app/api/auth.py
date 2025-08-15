"""
app/api/auth.py
Реализует функции для регистрации и аутентификации пользователей с использованием JWT.
"""
import logging
import uuid

from fastapi import APIRouter, HTTPException, Depends, Response, Cookie, status, Request
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from passlib.context import CryptContext

from app.api.dependencies import get_current_user
from app.core.rate_limiter import limiter
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
@limiter.limit("2/minute")
async def register(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация пользователя"""
    try:
        async with db.begin():
            existing_user = await get_user(db, user.username)
            if existing_user:
                logger.warning(f"Ошибка при регистрации пользователя: Пользователь с таким никнеймом уже "
                                 f"зарегистирирован")
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
            return UserResponse.model_validate(new_user)
    except Exception as e:
        logger.exception(f"Ошибка при регистрации пользователя: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка регистрации пользователя")


@router.post("/login/")
@limiter.limit("2/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db),
                response: Response = Response()):
    """Аутентификация и получение JWT токена"""
    try:
        user = await get_user(db, form_data.username)
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            logger.warning(f"Ошибка при аутентификации пользователя: Неверное имя пользователя или пароль.")
            raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль.")

        access_token = create_access_token({"sub": user.username})
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка авторизации. Подробнее: {e}")


@router.get("/me", summary="Получение информации текущего пользователя")
@limiter.limit("5/minute")
async def read_current_user(request: Request, current_user: UserModel = Depends(get_current_user)):
    """Возвращает информацию о текущем пользователе."""
    return UserResponse.model_validate(current_user)


@router.put("/me", summary="Обновление информации пользователя")
@limiter.limit("2/minute")
async def update_user_info(request: Request, user_update: UserUpdate,
                           current_user: UserModel = Depends(get_current_user),db: AsyncSession = Depends(get_db)):
    """Обновляет информацию текущего пользователя"""
    try:
        async with db.begin():
            existing_user = await get_user(db, user_update.username)
            if existing_user and existing_user.id != current_user.id:
                logger.warning(f"Ошибка при обновлении информации пользователя: Пользователя не существует")
                raise HTTPException(status_code=400, detail="Имя пользователя уже зарегистрировано")

            current_user.username = user_update.username
            current_user.hashed_password = pwd_context.hash(user_update.password)
            current_user.email = user_update.email
            current_user.additional_info = user_update.additional_info

            await db.commit()
            await db.refresh(current_user)
            return UserResponse.model_validate(current_user)
    except Exception as e:
        logger.exception(f"Ошибка при обновлении информации пользователя: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка обновления информации пользователя")


@router.get("/get_tokens")
@limiter.limit("2/minute")
async def get_tokens(request: Request, access_token: str = Cookie(None), refresh_token: str = Cookie(None)):
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh/")
@limiter.limit("2/minute")
async def refresh_token_endpoint(request: Request, refresh_token: str = Cookie(None), db: AsyncSession = Depends(get_db),
                                 response: Response = Response()):
    """Обновление access token с использованием refresh token"""
    try:
        if not refresh_token:
            logger.warning(f"Ошибка при обновлении токена: нет токена")
            raise HTTPException(status_code=400, detail="Refresh token is missing")

        refresh_token_record = await verify_refresh_token(db, refresh_token)
        if not refresh_token_record:
            logger.warning(f"Ошибка при обновлении токена: Токен не действителен")
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

        user_id = refresh_token_record.user_id  # Получаем пользователя из refresh token
        user = await db.scalar(select(User).where(User.id == user_id))
        if not user:
            logger.warning(f"Ошибка при обновлении токена: Пользователя не существует")
            raise HTTPException(status_code=404, detail="User not found")
        access_token = create_access_token({"sub": user.username, "user_id": user.id})

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
