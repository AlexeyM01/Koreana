"""
database.py
Устанавливает соединение с базой данных с помощью SQLAlchemy.
Реализует асинхронную инициализацию базы данных, что подходит для высоконагруженных приложений.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.future import select
from config import settings


Base = declarative_base()
DATABASE_URL = settings.database_url
engine = create_async_engine(DATABASE_URL, future=True, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """
    Инициализирует базу данных, создавая все таблицы в базе данных.

    Используется при запуске приложения для первоначальной настройки базы данных.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """
    Получает сессию базы данных.
    Returns:
        AsyncSession: Асинхронная сессия для работы с базой данных.
    """
    async with SessionLocal() as db:
        yield db


async def get_user(db: AsyncSession, username: str):
    """
    Получает пользователя по имени пользователя из базы данных.

    Args:
        db (AsyncSession): Асинхронная сессия базы данных.
        username (str): Имя пользователя для поиска.

    Returns:
        User: Объект пользователя, если найден, иначе None.
    """
    from models import User
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    return user

