import pytest

@pytest.mark.asyncio
async def test_db_connection(test_app, db_session):
    response = await db_session.execute("SELECT 1")
    assert response.scalar() == 1
