import pytest
from fastapi.testclient import TestClient
from services.users.api.main import app
import uuid

client = TestClient(app)

@pytest.fixture
def test_user():
    email = f"testuser_{uuid.uuid4().hex[:8]}@qa.com"
    password = "TestPass123!"
    full_name = "QA User"
    return {"email": email, "password": password, "full_name": full_name}

def test_registration_login_and_me(test_user):
    # 1. Registro de usuario
    resp = client.post("/api/v1/auth/register", json=test_user)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["email"] == test_user["email"]

    # 2. Login exitoso
    login_data = {"username": test_user["email"], "password": test_user["password"]}
    resp = client.post("/api/v1/auth/token", data=login_data)
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    assert token

    # 3. Login fallido
    bad_login = {"username": test_user["email"], "password": "wrongpass"}
    resp = client.post("/api/v1/auth/token", data=bad_login)
    assert resp.status_code == 401

    # 4. Consulta de usuario autenticado
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200, resp.text
    user_data = resp.json()
    assert user_data["email"] == test_user["email"]
