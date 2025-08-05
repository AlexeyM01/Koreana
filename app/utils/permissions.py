"""
app/utils/permissions.py
"""

from fastapi import Depends, HTTPException
from fastapi_users import jwt
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User as UserModel, Role

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def verify_token(token: str):
    """Функция для проверки JWT токена и возвращает полезную нагрузку, если верный токен"""
    # TO-DO Добавить проверку токенов в основную работу
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def permission_dependency(permission: str):

    async def check_permission_dependency(current_user: UserModel = Depends(get_current_user),
                                          db: AsyncSession = Depends(get_db)):
        # Получаем роль пользователя по его role_id
        query = await db.execute(select(Role).where(Role.id == current_user.role_id))
        result = query.scalars().first()

        if not result:
            raise HTTPException(status_code=403, detail="Роль не найдена")
        if permission not in result.permissions:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return True

    return check_permission_dependency

