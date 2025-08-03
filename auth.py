"""
auth.py
Реализует функции для регистрации и аутентификации пользователей с использованием JWT.
"""

from fastapi import APIRouter, HTTPException, Depends, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from passlib.context import CryptContext
from starlette.responses import HTMLResponse
from models import User as UserModel, Role as RoleModel, Role
from database import get_db, get_user
from schemas import UserCreate, UserResponse, UserUpdate, RoleCreate, RoleUpdate, RoleResponse
from config import settings
from dependencies import get_current_user, check_permission

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Извлечение конфигурационных данных
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def create_access_token(username: str):
    """Функция для создания JWT токена"""

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": username}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """Функция для проверки JWT токена и возвращает полезную нагрузку, если верный токен"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


@router.post("/registration/", response_model=UserResponse, summary="Создание пользователя")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Регистрация пользователя"""
    async with db.begin():
        existing_user = await get_user(db, user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким никнеймом уже зарегистирирован")

        # Хэшируем пароль
        hashed_password = pwd_context.hash(user.password)
        new_user = UserModel(
            username=user.username,
            hashed_password=hashed_password,
            registered_at=datetime.utcnow(),
            email=user.email,
            is_active=True,
            is_superuser=False,
            is_verified=False,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return UserResponse.from_orm(new_user)


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db),
                response: Response = Response()):
    """Аутентификация и получение JWT токена"""
    try:
        user = await get_user(db, form_data.username)
        if not user or not pwd_context.verify(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль.")

        access_token = create_access_token(user.username)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax",
            secure=True
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка {e}")


@router.get("/me", response_model=UserResponse, summary="Получение информации текущего пользователя")
async def read_users_me(current_user: UserModel = Depends(get_current_user)):
    """Возвращает информацию о текущем пользователе."""
    return current_user


@router.get("/secure-data")
async def read_secure_data(access_token: str = Cookie(None), current_user: UserModel = Depends(get_current_user)):
    """Извлекает защищенные данные, проверяя токен из cookie-файла."""
    return {"message": "Это безопасные данные.", "user": current_user.username}


@router.put("/me", response_model=UserResponse, summary="Обновление информации пользователя")
async def update_user_info(user_update: UserUpdate, current_user: UserModel = Depends(get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """Обновляет информацию текущего пользователя"""
    async with db.begin():
        try:
            existing_user = await get_user(db, user_update.username)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(status_code=400, detail="Имя пользователя уже зарегистрировано")

            current_user.username = user_update.username
            current_user.hashed_password = pwd_context.hash(user_update.password)
            current_user.email = user_update.email
            current_user.additional_info = user_update.additional_info

            await db.commit()
            await db.refresh(current_user)
            return UserResponse.from_orm(current_user)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Возникла ошибка {e}.")


def permission_dependency(permission: str):
    """Функция-фабрика для создания зависимостей разрешений."""

    async def check_permission_dependency(current_user: UserModel = Depends(get_current_user),
                                          db: AsyncSession = Depends(get_db)):
        # Получаем роль пользователя по его role_id
        result = await db.execute(select(Role).where(Role.id == current_user.role_id))
        result = result.scalars().first()

        if not result:
            raise HTTPException(status_code=403, detail="Роль не найдена")
        if permission not in result.permissions:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return True

    return check_permission_dependency


@router.post("/roles/", response_model=RoleResponse)
async def create_role(role: RoleCreate, db: AsyncSession = Depends(get_db),
                      has_permission: bool = Depends(permission_dependency("manage_users"))):
    """Создает новую роль с проверкой на разрешение"""
    try:
        db_role = RoleModel(**role.model_dump())
        db.add(db_role)
        await db.commit()
        await db.refresh(db_role)
        return RoleResponse.from_orm(db_role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def read_role(role_id: int, db: AsyncSession = Depends(get_db),
                    has_permission: bool = Depends(permission_dependency("manage_users"))):
    """Возвращает роль по ID с проверкой на разрешение"""
    try:
        from sqlalchemy import select
        result = await db.execute(select(RoleModel).where(RoleModel.id == role_id))
        role = result.scalars().first()
        if role is None:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        return RoleResponse.from_orm(role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(role_id: int, role: RoleUpdate, db: AsyncSession = Depends(get_db),
                      has_permission: bool = Depends(permission_dependency("manage_users"))):
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
        return RoleResponse.from_orm(db_role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")


@router.delete("/roles/{role_id}", response_model=RoleResponse)
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db),
                      has_permission: bool = Depends(permission_dependency("manage_users"))):
    """Удаляет роль по ID."""
    try:
        from sqlalchemy import select
        result = await db.execute(select(RoleModel).where(RoleModel.id == role_id))
        db_role = result.scalars().first()

        if db_role is None:
            raise HTTPException(status_code=404, detail="Роль не найдена")
        await db.delete(db_role)
        await db.commit()
        return RoleResponse.from_orm(db_role)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Произошла ошибка {e}")
