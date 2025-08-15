"""
app/api/roles.py

"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

import logging

from app.core.database import get_db
from app.schemas.role_schemas import RoleResponse, RoleCreate, RoleUpdate
from app.models.models import Role as RoleModel
from app.utils.permissions import permission_dependency
from app.core.rate_limiter import limiter

router = APIRouter(prefix="/roles")

logger = logging.getLogger(__name__)


@router.post("/")
@limiter.limit("5/minute")
async def create_role(request: Request, role: RoleCreate, db: AsyncSession = Depends(get_db),
                      has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Создает новую роль с проверкой на разрешение"""
    try:
        db_role = RoleModel(**role.model_dump())
        db.add(db_role)
        await db.commit()
        await db.refresh(db_role)
        logger.info(f"Создана новая роль: {db_role.name}")
        return RoleResponse.model_validate(db_role)
    except Exception as e:
        logger.exception(f"Ошибка при создании роли: {e}")
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.get("/{role_id}")
@limiter.limit("20/minute")
async def read_role(request: Request, role_id: int, db: AsyncSession = Depends(get_db),
                    has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Возвращает роль по ID с проверкой на разрешение"""
    try:
        from sqlalchemy import select
        result = await db.execute(select(RoleModel).where(RoleModel.id == role_id))
        role = result.scalars().first()
        if role is None:
            logger.warning(f"Ошибка при чтении роли: Роль с ID {role_id} не найдена")
            raise HTTPException(status_code=404, detail="Роль не найдена")
        logger.debug(f"Роль успешно прочитана: {role.name}, ID: {role_id}")
        return RoleResponse.model_validate(role)
    except Exception as e:
        logger.exception(f"Ошибка при чтении роли: {e}")
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.put("/{role_id}")
@limiter.limit("5/minute")
async def update_role(request: Request, role_id: int, role: RoleUpdate, db: AsyncSession = Depends(get_db),
                      has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Обновляет роль по ID"""
    try:
        from sqlalchemy import select
        result = await db.execute(select(RoleModel).where(RoleModel.id == role_id))
        role = result.scalars().first()
        if role is None:
            logger.warning(f"Ошибка при обновлении роли: Роль с ID {role_id} не найдена")
            raise HTTPException(status_code=404, detail="Роль не найдена")

        for key, value in role.model_dump(exclude_unset=True).items():
            setattr(role, key, value)

        await db.commit()
        await db.refresh(role)
        logger.info(f"Роль успешно обновлена: {role.name}, ID: {role_id}")
        return RoleResponse.model_validate(role)
    except Exception as e:
        logger.exception(f"Ошибка при обновлении роли: {e}")
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.delete("/{role_id}")
@limiter.limit("5/minute")
async def delete_role(request: Request, role_id: int, db: AsyncSession = Depends(get_db),
                      has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Удаляет роль по ID."""
    try:
        from sqlalchemy import select
        result = await db.execute(select(RoleModel).where(RoleModel.id == role_id))
        db_role = result.scalars().first()

        if db_role is None:
            logger.warning(f"Ошибка при удалении роли: Роль с ID {role_id} не найдена")
            raise HTTPException(status_code=404, detail="Роль не найдена")
        await db.delete(db_role)
        await db.commit()
        logger.info(f"Роль успешно удалена: {db_role.name}, ID: {role_id}")
        return RoleResponse.model_validate(db_role)
    except Exception as e:
        logger.exception(f"Ошибка при удалении роли: {e}")
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")
