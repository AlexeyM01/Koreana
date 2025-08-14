"""
app/services/user_services.py
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


async def get_user(db: AsyncSession, username: str):
    """
    Получает пользователя по имени пользователя из базы данных.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        username (str): Имя пользователя для поиска.

    Returns:
        User: Объект пользователя, если найден, иначе None.
    """
    # Не удалять импорт, возможна ошибка: ImportError: cannot import name 'User' from partially initialized module
    # 'models' (most likely due to a circular import)
    from app.models.models import User
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    return user
