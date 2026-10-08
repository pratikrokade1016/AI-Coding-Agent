from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_user():
    response = client.post(
        "/users/",
        params={
            "username": "pratik",
            "email": "pratik@example.com",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["username"] == "pratik"
    assert data["email"] == "pratik@example.com"