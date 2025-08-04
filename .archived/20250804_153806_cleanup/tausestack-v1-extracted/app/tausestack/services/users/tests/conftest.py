import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from services.users.api.main import app
from services.users.core.db_models import Base
from services.users.core.auth import auth_provider

# Configuración de base de datos en memoria para pruebas
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Mock de Supabase Auth
@pytest.fixture
def mock_supabase_auth():
    mock = AsyncMock()
    # Configurar mocks para los métodos de autenticación
    mock.get_user.return_value = {
        "user": {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {"name": "Test User"},
            "app_metadata": {"roles": ["user"]}
        },
        "session": {"access_token": "test-token"}
    }
    return mock

# Cliente de prueba de FastAPI
@pytest.fixture
def test_client():
    # Crear tablas en la base de datos de prueba
    Base.metadata.create_all(bind=engine)
    
    # Sobrescribir la dependencia de base de datos para usar la de prueba
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Limpiar después de las pruebas
    Base.metadata.drop_all(bind=engine)

# Fixture para usuario autenticado
@pytest.fixture
def authenticated_client(test_client, monkeypatch):
    # Mockear la validación de token para simular usuario autenticado
    mock_validate = MagicMock(return_value={
        "sub": "test-user-id",
        "email": "test@example.com",
        "user_metadata": {"name": "Test User"},
        "app_metadata": {"roles": ["user"]}
    })
    
    monkeypatch.setattr(auth_provider, "validate_token", mock_validate)
    
    # Añadir token de prueba a las cabeceras
    test_client.headers.update({"Authorization": "Bearer test-token"})
    return test_client
