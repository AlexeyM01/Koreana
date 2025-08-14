"""
app/utils/permissions.py
"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.models import User as UserModel, Role
from app.core.rate_limiter import limiter

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


def permission_dependency(permission: str):

    async def check_permission_dependency(request: Request, current_user: UserModel = Depends(get_current_user),
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
