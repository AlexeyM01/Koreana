"""
schemas.py
Определяет входные схемы данных с помощью Pydantic.
Упрощает валидацию входящих данных для создания пользователей, комментариев и задач."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr


class Priority(str, Enum):
    """Документация"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UserCreate(BaseModel):
    """Документация"""
    username: str
    password: str
    email: EmailStr


class UserUpdate(BaseModel):
    """Документация"""
    username: str
    password: str
    email: EmailStr
    additional_info: Optional[str] = None
    role_id: int

    class Config:
        """Документация"""
        from_attributes = True


class UserResponse(BaseModel):
    """Документация"""
    id: int
    username: str
    email: EmailStr
    role_id: int
    registered_at: datetime
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    class Config:
        """Документация"""
        from_attributes = True


class CommentCreate(BaseModel):
    """Документация"""
    task_id: int
    content: str


class TaskCreate(BaseModel):
    """Документация"""
    title: str
    priority: Optional[Priority] = Priority.MEDIUM


class TaskUpdate(BaseModel):
    """Документация"""
    title: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[Priority] = None
