"""
app/schemas/role_schemas.py
Определяет схемы данных ролей пользователей.
"""

from pydantic import BaseModel
from typing import List, Optional


class RoleCreate(BaseModel):
    pass
    name: str
    permissions: List[str] = []


class RoleUpdate(BaseModel):
    pass
    name: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleResponse(BaseModel):
    pass
    id: int
    name: str
    permissions: List[str]

    class Config:
        from_attributes = True
