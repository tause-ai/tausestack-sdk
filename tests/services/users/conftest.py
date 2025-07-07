import os
import subprocess
import pytest
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from alembic.config import Config
from alembic import command
from services.users.core.db_models import Base
import uuid # Added for test_user fixture

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

# --- Fixtures de Pytest (Primera versión observada) ---

@pytest.fixture(scope="session")
def db_engine_v1(): # Renamed to avoid conflict
    """Crea el motor de SQLAlchemy para la base de datos de test."""
    db_url = get_test_db_url()
    engine = create_engine(db_url)
    create_tables(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session_v1(db_engine_v1): # Renamed and uses renamed engine
    """Crea una sesión de base de datos para cada test."""
    connection = db_engine_v1.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client_v1(db_session_v1): # Renamed and uses renamed session
    """Crea un cliente de prueba para la API."""
    from services.users.main import app # Assuming this is the correct app
    from services.users.core.deps import get_db
    
    def override_get_db():
        try:
            yield db_session_v1
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client

# --- Fixtures de Pytest (Segunda versión observada - parece más actual o refactorizada) ---
# The run_migrations function was mentioned but not fully defined in the provided snippet.
# Assuming it's defined elsewhere or should be mocked/removed if not used by current tests.
def run_migrations():
    # Placeholder: Actual migration logic would go here
    # For example, using alembic:
    # alembic_cfg = Config("alembic.ini") # Ensure alembic.ini is configured for tests
    # command.upgrade(alembic_cfg, "head")
    print("Placeholder: run_migrations() called")
    pass

@pytest.fixture(scope="session")
def db_engine(): # This will be the primary db_engine
    """Proporciona un motor de base de datos para la sesión de tests, aplicando migraciones."""
    engine = create_engine(get_test_db_url())
    # Aplica migraciones al inicio de la sesión de tests
    # drop_all_tables(engine) # Optional: ensure clean state before migrations
    # create_tables(engine) # Or use migrations if they handle table creation
    run_migrations() # Assuming this sets up the schema
    yield engine
    # No cerramos la conexión explícitamente aquí para permitir múltiples tests,
    # pero dispose() es buena práctica al final de la sesión si no hay más usos.
    # engine.dispose() # Consider if needed based on test runner behavior

@pytest.fixture(scope="function")
def db_session(db_engine): # This will be the primary db_session
    """Proporciona una sesión de base de datos limpia para cada test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = scoped_session(sessionmaker(bind=connection))
    db = Session()
    yield db
    db.close() # Ensure session is closed
    Session.remove()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module") # Changed scope to module as per second definition
def client(db_engine): # Uses the primary db_engine
    """Proporciona un cliente de prueba de FastAPI."""
    # Ensure services.users.api.main or services.users.main is the correct app
    # The original snippet had both. Assuming services.users.main for consistency with client_v1
    # If services.users.api.main is different, this might need adjustment or a separate fixture.
    from services.users.main import app 
    from services.users.core.deps import get_db # For overriding
    from fastapi.testclient import TestClient

    # Override DB dependency for the app used by TestClient
    def override_get_db_for_test_client():
        # This needs to provide a session similar to how db_session does,
        # but scoped for the client's usage. Using db_engine to create a new session for client.
        conn = db_engine.connect()
        txn = conn.begin()
        sess_factory = sessionmaker(bind=conn)
        sess = scoped_session(sess_factory)
        try:
            yield sess
        finally:
            sess.remove()
            txn.rollback()
            conn.close()

    app.dependency_overrides[get_db] = override_get_db_for_test_client
    
    # os.environ["TAUSESTACK_DB_URL"] = get_test_db_url() # Setting this might be redundant if app uses get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up dependency override after client fixture is done
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture
def test_user(): # This will be the primary test_user
    """Proporciona datos de usuario de prueba."""
    return {
        "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
        "full_name": "Test User",
        "password": "TestPass123!"
    }
