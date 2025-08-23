"""
app/utils/permissions.py
"""
import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User as UserModel, Role

logger = logging.getLogger(__name__)
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def permission_dependency(permission: str):
    async def check_permission_dependency(request: Request, current_user: UserModel = Depends(get_current_user),
                                          db: AsyncSession = Depends(get_db)):
        # Получаем роль пользователя по его role_id
        role = await db.scalar(select(Role).where(Role.id == current_user.role_id))

        if not role:
            logger.warning(f"Ошибка проверки разрешений: Роль не найдена для пользователя {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Роль не найдена")
        logger.warning(f"Ошибка проверки разрешений: Роль не найдена для пользователя {current_user.username}")

        if permission not in role.permissions:
            logger.warning(f"Ошибка проверки разрешений: У пользователя {current_user.username} нет прав {permission}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")
        logger.debug(f"Проверка разрешений успешно пройдена для пользователя {current_user.username},"
                     f"требуется разрешение: {permission}")
        return True

    return check_permission_dependency
