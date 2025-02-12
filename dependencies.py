"""
dependencies.py
Содержит зависимости для FastAPI, включая получение текущего пользователя по токену.
Реализует обработку ошибок аутентификации, возвращая HTTP 401, если пользователь невалиден.
"""

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from config import settings
from database import get_user, get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Получает текущего пользователя по токену.

    Args:
        token (str): Токен аутентификации.
        db (AsyncSession): Сессия базы данных.

    Returns:
        User: Объект пользователя, если аутентификация успешна.

    Raises:
        HTTPException: Если аутентификация не удалась.
    """
    try:
        credentials = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username = credentials.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Credentials not valid")

        user = await get_user(db, username)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        return user

    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
