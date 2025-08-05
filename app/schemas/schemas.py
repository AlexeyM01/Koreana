"""
app/schemas/schemas.py
Определяет входные схемы данных с помощью Pydantic.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class Priority(str, Enum):
    """Документация"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CommentCreate(BaseModel):
    task_id: int
    content: str


class TaskCreate(BaseModel):
    title: str
    priority: Optional[Priority] = Priority.MEDIUM


class TaskUpdate(BaseModel):
    completed: Optional[bool] = None
    priority: Optional[Priority] = None
