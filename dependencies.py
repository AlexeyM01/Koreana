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
from models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


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
            raise HTTPException(status_code=401, detail="Учетные данные недействительны")

        user = await get_user(db, username)
        if user is None:
            raise HTTPException(status_code=401, detail="Недействительные учетные данные аутентификации")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Не удалось проверить учетные данные")


async def check_permission(permission: str, current_user: User = Depends(get_current_user)):
    """Проверяет, имеет ли пользователь указанное разрешение."""
    if permission not in current_user.role.permissions:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return True
