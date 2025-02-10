def test_create_user(client):
    response = client.post("/users/", json={"username": "testuser", "password": "password"})
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"

def test_read_tasks(client):
    response = client.get("/tasks/?skip=0&limit=10")
    assert response.status_code == 200
