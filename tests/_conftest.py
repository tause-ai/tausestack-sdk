import os
import subprocess
import pytest
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from alembic.config import Config
from alembic import command
from services.users.core.db_models import Base

# --- Configuración de la base de datos de test ---

def get_test_db_url() -> str:
    """Obtiene la URL de la base de datos de test desde variables de entorno."""
    test_db_url = os.getenv("TAUSESTACK_TEST_DB_URL")
    if not test_db_url:
        raise ValueError("TAUSESTACK_TEST_DB_URL no está definida en el entorno")
    return test_db_url

def create_tables(engine):
    """Crea todas las tablas en la base de datos."""
    Base.metadata.create_all(bind=engine)

def drop_all_tables(engine):
    """Elimina todas las tablas de la base de datos de test."""
    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(bind=engine)

# --- Fixtures de Pytest ---

@pytest.fixture(scope="session")
def db_engine():
    """Crea el motor de SQLAlchemy para la base de datos de test."""
    # Obtener la URL de la base de datos de test
    db_url = get_test_db_url()
    
    # Crear el motor
    engine = create_engine(db_url)
    
    # Crear todas las tablas
    create_tables(engine)
    
    yield engine
    
    # Limpiar después de las pruebas
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Crea una sesión de base de datos para cada test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)
    
    yield session
    
    # Limpiar después del test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Crea un cliente de prueba para la API."""
    from services.users.main import app
    from services.users.core.deps import get_db
    
    # Sobrescribir la dependencia de la base de datos
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="function")
def test_user():
    """Proporciona datos de prueba para un usuario."""
    return {
        "email": f"testuser_{os.urandom(4).hex()}@example.com",
        "full_name": "Test User",
        "password": "TestPass123!"
    }
    engine = create_engine(get_test_db_url())
    # Aplica migraciones al inicio de la sesión de tests
    run_migrations()
    yield engine
    # No cerramos la conexión para permitir múltiples ejecuciones

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Proporciona una sesión de base de datos limpia para cada test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = scoped_session(sessionmaker(bind=connection))
    
    yield Session()
    
    # Limpieza después del test
    Session.remove()
    transaction.rollback()
    connection.close()

# Fixture para FastAPI TestClient
@pytest.fixture(scope="module")
def client():
    """Proporciona un cliente de prueba de FastAPI."""
    from services.users.api.main import app
    from fastapi.testclient import TestClient
    
    # Sobrescribe la URL de la base de datos para tests
    os.environ["TAUSESTACK_DB_URL"] = get_test_db_url()
    
    with TestClient(app) as test_client:
        yield test_client

# Fixture para datos de prueba
@pytest.fixture
def test_user():
    """Proporciona datos de usuario de prueba."""
    return {
        "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
        "full_name": "Test User",
        "password": "TestPass123!"
    }
