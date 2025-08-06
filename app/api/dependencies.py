"""
app/api/dependencies.py
Содержит зависимости для FastAPI, включая получение текущего пользователя по токену.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.services.user_service import get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Возникла ошибка ExpiredSignatureError. Подробнее: {e}")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Возникла ошибка InvalidTokenError. Подробнее: {e}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Возникла ошибка {e}")
