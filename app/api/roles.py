"""
app/api/roles.py

"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

import logging

from app.core.database import get_db
from app.schemas.role_schemas import RoleResponse, RoleCreate, RoleUpdate
from app.models.models import Role as RoleModel, User as UserModel
from app.utils.permissions import permission_dependency
from app.core.rate_limiter import limiter


router = APIRouter(prefix="/roles")

logger = logging.getLogger(__name__)


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
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
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Ошибка при создании роли: {e}")
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.get("/{role_id}", response_model=RoleResponse)
@limiter.limit("20/minute")
async def read_role(request: Request, role_id: int, db: AsyncSession = Depends(get_db),
                    has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Возвращает роль по ID с проверкой на разрешение"""
    try:
        result = await db.execute(select(RoleModel).where(RoleModel.id == role_id))
        role = result.scalars().first()
        if role is None:
            logger.warning(f"Ошибка при чтении роли: Роль с ID {role_id} не найдена")
            raise HTTPException(status_code=404, detail="Роль не найдена")
        logger.debug(f"Роль успешно прочитана: {role.name}, ID: {role_id}")
        return RoleResponse.model_validate(role)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Ошибка при чтении роли: {e}")
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.put("/{role_id}", response_model=RoleResponse)
@limiter.limit("5/minute")
async def update_role(request: Request, role_id: int, role_update: RoleUpdate, db: AsyncSession = Depends(get_db),
                      has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Обновляет роль по ID"""
    try:
        result = await db.execute(select(RoleModel).where(RoleModel.id == role_id))
        role = result.scalars().first()
        if role is None:
            logger.warning(f"Ошибка при обновлении роли: Роль с ID {role_id} не найдена")
            raise HTTPException(status_code=404, detail="Роль не найдена")

        if role_update.name is not None:
            role.name = role_update.name
        if role_update.permissions is not None:
            role.permissions = role_update.permissions

        db.add(role)
        logger.info(f"Роль успешно обновлена: {role.name}, ID: {role_id}")
        return RoleResponse.model_validate(role)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Ошибка при обновлении роли: {e}")
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.delete("/{role_id}", response_model=RoleResponse)
@limiter.limit("5/minute")
async def delete_role(request: Request, role_id: int, db: AsyncSession = Depends(get_db),
                      has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Удаляет роль по ID."""
    try:
        result = await db.execute(select(RoleModel).where(RoleModel.id == role_id))
        db_role = result.scalars().first()

        if db_role is None:
            logger.warning(f"Ошибка при удалении роли: Роль с ID {role_id} не найдена")
            raise HTTPException(status_code=404, detail="Роль не найдена")
        await db.delete(db_role)
        logger.info(f"Роль успешно удалена: {db_role.name}, ID: {role_id}")
        return RoleResponse.model_validate(db_role)
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Ошибка при удалении роли: {e}")
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.post("/{role_id}/permissions", response_model=RoleResponse)
async def add_permissions_to_role(request: Request, role_id: int, permissions: List[str],
                                  db: AsyncSession = Depends(get_db),
                                  has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Добавляет разрешения к роли."""
    try:
        role = await db.scalar(select(RoleModel).where(RoleModel.id == role_id))

        if not role:
            logger.warning(f"Роль с ID {role_id} не найдена")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не найдена")

        if role.permissions is None:
            role.permissions = []
        for permission in permissions:
            if permission not in role.permissions:
                role.permissions.append(permission)

        db.add(role)

        logger.info(f"К роли {role.name} добавлены разрешения: {permissions}")
        return RoleResponse.model_validate(role)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Ошибка при добавлении разрешений к роли: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Произошла ошибка при добавлении разрешений")


@router.delete("/{role_id}/permissions", response_model=RoleResponse)
async def remove_permissions_from_role(request: Request, role_id: int, permissions: List[str],
                                       db: AsyncSession = Depends(get_db),
                                       has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Удаляет разрешения у роли."""
    try:
        role = await db.scalar(select(RoleModel).where(RoleModel.id == role_id))
        if not role:
            logger.warning(f"Роль с ID {role_id} не найдена")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не найдена")

        if role.permissions is not None:
            role.permissions = [p for p in role.permissions if p not in permissions]

        db.add(role)

        logger.info(f"У роли {role.name} удалены разрешения: {permissions}")
        return RoleResponse.model_validate(role)

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Ошибка при удалении разрешений у роли: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Произошла ошибка при удалении разрешений")


@router.put("/user/{user_id}/role/{role_id}", summary="Присвоение роли пользователю")
async def assign_role_to_user(request: Request, user_id: int, role_id: int, db: AsyncSession = Depends(get_db),
                              has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Присваивает указанную роль пользователю."""
    try:
        user = await db.scalar(select(UserModel).where(UserModel.id == user_id))
        if not user:
            logger.warning(f"Пользователь с ID {user_id} не найден.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

        role = await db.scalar(select(RoleModel).where(RoleModel.id == role_id))
        if not role:
            logger.warning(f"Роль с ID {role_id} не найдена.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Роль не найдена")

        user.role_id = role_id
        db.add(user)

        logger.info(f"Пользователю {user.username} присвоена роль {role.name}.")
        return {"message": f"Роль успешно присвоена пользователю {user.username}"}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Ошибка при присвоении роли пользователю: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Произошла ошибка при присвоении роли")


@router.get("/", response_model=List[RoleResponse])
@limiter.limit("20/minute")
async def get_all_roles(request: Request, db: AsyncSession = Depends(get_db),
                        has_permission: bool = Depends(permission_dependency('manage_users'))):
    """Возвращает список всех ролей с проверкой на разрешение."""
    try:
        result = await db.execute(select(RoleModel))
        roles = result.scalars().all()
        logger.debug("Список всех ролей успешно получен.")
        return [RoleResponse.model_validate(role) for role in roles]
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Ошибка при получении списка ролей: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Произошла ошибка при получении списка ролей")
