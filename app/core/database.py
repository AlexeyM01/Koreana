"""
app/core/database.py
Устанавливает соединение с базой данных с помощью SQLAlchemy.
Реализует асинхронную инициализацию базы данных, что подходит для высоконагруженных приложений.
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings
import redis.asyncio as redis
import logging

Base = declarative_base()
DATABASE_URL = settings.database_url
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
redis_client = redis.Redis.from_url(settings.redis_host, decode_responses=True)
# decode_responses=True for string keys/values

logger = logging.getLogger("app")


async def init_db():
    """
    Инициализирует базу данных, создавая все таблицы в базе данных.
    """
    max_retries = 5  # Количество попыток
    retry_delay_sec = 5  # Задержка между попытками в секундах
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Инициализация базы данных успешно завершена.")
            return
        except Exception as e:
            logger.error(f"Попытка {attempt + 1} не окончилась успехом к подключении к базе данных: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay_sec)
            else:
                logger.critical("Достигнуто максимальное количество повторных попыток."
                                "Не удалось инициализировать базу данных.")
                raise e


async def get_db() -> AsyncSession:
    """
    Получает сессию базы данных.
    """
    session = async_session()
    logger.info("Создана новая сессия базы данных")
    try:
        yield session
        await session.commit()
        logger.info("Сессия базы данных успешно завершена и закрыта")
    except Exception as e:
        await session.rollback()
        logger.exception(f"Произошла ошибка, откат сессии: {e}")
        raise
    finally:
        await session.close()
        logger.info("Сессия базы данных закрыта")


async def get_redis() -> redis.Redis:
    """
    Получает клиента Redis.
    """
    return redis_client
