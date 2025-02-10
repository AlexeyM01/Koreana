import pytest

@pytest.mark.asyncio
async def test_register_user(test_app, db_session):
    response = test_app.post("/registration/", json={
        "username": "testuser",
        "password": "testpassword",
        "email": "testuser@example.com"
    })
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
