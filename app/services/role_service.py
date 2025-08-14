"""
app/services/role_services.py

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
# TODO Разделить логику от бизнес-задач

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
        return RoleResponse.model_validate(db_role)
    except Exception as e:
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
            logger.exception(f"Ошибка при чтении роли: Роли не существует")
            raise HTTPException(status_code=404, detail="Роль не найдена")
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
        db_role = result.scalars().first()
        if db_role is None:
            raise HTTPException(status_code=404, detail="Роль не найдена")

        for key, value in role.model_dump(exclude_unset=True).items():
            setattr(db_role, key, value)

        await db.commit()
        await db.refresh(db_role)
        return RoleResponse.model_validate(db_role)
    except Exception as e:
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
            raise HTTPException(status_code=404, detail="Роль не найдена")
        await db.delete(db_role)
        await db.commit()
        return RoleResponse.model_validate(db_role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")
