import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from main import app
from database import init_db, get_db


@pytest.fixture(scope="module")
async def test_app():
    await init_db()

    yield TestClient(app)


@pytest.fixture(scope="function")
async def db_session(test_app):
    async with get_db() as session:  # Получаем сессию базы данных
        yield session
