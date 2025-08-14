"""
app/schemas/user_schemas.py
Определяет схемы данных пользователей.
"""
from datetime import datetime
from typing import Optional

from pydantic import EmailStr, BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    """Базовая модель для пользователя, содержащая общие поля."""
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase):
    """Модель для создания пользователя на основе класса UserBase."""
    password: str

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(UserBase):
    """Модель для обновления информации о пользователе на основе класса UserBase."""
    password: str
    additional_info: Optional[str] = None
    role_id: int

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """Модель для ответа с информацией о пользователе на основе класса UserBase."""
    id: int
    role_id: int
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    model_config = ConfigDict(from_attributes=True)
