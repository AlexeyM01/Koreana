"""
app/api/dependencies.py
Содержит зависимости для FastAPI, включая получение текущего пользователя по токену.
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import jwt
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.user_service import get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
logger = logging.getLogger(__name__)


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Получает текущего пользователя по токену.
    """
    try:
        credentials = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username = credentials.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Учетные данные недействительны")

        user = await get_user(db, username)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Недействительные учетные данные аутентификации")
        return user

    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Попытка доступа с просроченным токеном: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Срок действия токена истек")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Попытка доступа с недействительным токеном: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Недействительный токен")
    except Exception as e:
        logger.exception(f"Ошибка при получении текущего пользователя: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка аутентификации")
