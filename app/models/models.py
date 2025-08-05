"""
app/models/models.py
Определяет модели пользователя и пользовательских ролей.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (TIMESTAMP, Boolean, Column, ForeignKey, Integer,
                        String, ARRAY)
from app.core.database import Base


class User(Base):
    """Класс для определения таблицы пользователей"""
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String(length=1024), nullable=False)
    email = Column(String, nullable=False, unique=True)
    role_id: int = Column(Integer, ForeignKey('role.id'), nullable=False, default=1)
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False, nullable=False)
    is_verified: bool = Column(Boolean, default=False, nullable=False)
    additional_info: Optional[str] = Column(String, nullable=True)


class Role(Base):
    """Класс для определения таблицы ролей"""
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True)
    permissions = Column(ARRAY(String), nullable=True)
    '''
    (1, 'STUDENT'),
    (2, 'TEACHER'),
    (3, 'ADMIN'),
    (4, 'PARENT'),
    (5, 'MANAGER'),
    (6, 'OBSERVER')
    '''
