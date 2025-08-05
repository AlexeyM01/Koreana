"""
app/core/database.py
Устанавливает соединение с базой данных с помощью SQLAlchemy.
Реализует асинхронную инициализацию базы данных, что подходит для высоконагруженных приложений.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings


Base = declarative_base()
DATABASE_URL = settings.database_url
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


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
    async with async_session() as session:
        yield session




