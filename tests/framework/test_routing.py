import os
import pytest
from fastapi import FastAPI, APIRouter, Request, Response, HTTPException
from fastapi.testclient import TestClient
from pathlib import Path

from tausestack.framework.routing import load_routers_from_directory, TauseStackRouter, TauseStackRoute

@pytest.fixture
def app_for_router_loading():
    """Provides a FastAPI app instance for router loading tests."""
    return FastAPI()

@pytest.fixture
def temp_router_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for router files."""
    router_dir = tmp_path / "routes"
    router_dir.mkdir()
    return router_dir


def test_load_routers_successfully(temp_router_dir: Path):
    """Verify that two separate routers are loaded correctly."""
    # Router 1: /users
    (temp_router_dir / "users_routes.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/users')\n"
        "def get_users(): return {'users': []}"
    )

    # Router 2: /products
    (temp_router_dir / "products_routes.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(prefix='/products', tags=['products'])\n"
        "@router.get('/')\n"
        "def get_products(): return {'products': []}"
    )

    app = FastAPI()
    loaded = load_routers_from_directory(app, str(temp_router_dir))

    assert sorted(loaded) == sorted(["users_routes", "products_routes"])

    client = TestClient(app)
    response_users = client.get("/users")
    assert response_users.status_code == 200
    assert response_users.json() == {"users": []}

    response_products = client.get("/products/")
    assert response_products.status_code == 200
    assert response_products.json() == {"products": []}

def test_ignore_file_without_router(temp_router_dir: Path):
    """Verify that a .py file without an APIRouter instance is ignored."""
    (temp_router_dir / "utils.py").write_text(
        "def helper_function(): return 'I am a helper'"
    )

    app = FastAPI()
    loaded = load_routers_from_directory(app, str(temp_router_dir))
    assert loaded == []

def test_ignore_non_python_files(temp_router_dir: Path):
    """Verify that non-.py files are ignored."""
    (temp_router_dir / "notes.txt").write_text("this is not a router.")

    app = FastAPI()
    loaded = load_routers_from_directory(app, str(temp_router_dir))
    assert loaded == []

def test_handle_non_existent_directory():
    """Verify that a non-existent directory is handled gracefully."""
    app = FastAPI()
    # Assuming the function prints a warning, we can check stdout or just ensure no crash
    loaded = load_routers_from_directory(app, "/non/existent/path")
    assert loaded == []

def test_router_with_syntax_error(temp_router_dir: Path, capsys):
    """Verify that a file with a syntax error is handled gracefully."""
    (temp_router_dir / "broken_route.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter()\n"
        "@router.get('/broken')\n"
        "def get_broken() return {'status': 'oops'}"  # Syntax error: missing ':'
    )

    app = FastAPI()
    loaded = load_routers_from_directory(app, str(temp_router_dir))
    assert loaded == []

    captured = capsys.readouterr()
    assert "Error loading router from 'broken_route.py'" in captured.out


def test_create_tausestack_router():
    from tausestack.framework.routing import TauseStackRoute # Diagnostic import
    """Test basic creation of TauseStackRouter."""
    router = TauseStackRouter()
    assert isinstance(router, APIRouter)
    assert router.route_class is TauseStackRoute  # Ensure TauseStackRoute is imported at the top
    assert hasattr(router, 'auth_required')
    assert router.auth_required is False

def test_create_tausestack_router_with_auth_flag():
    """Test that the TauseStackRouter class correctly sets the auth flag."""
    router = TauseStackRouter(auth_required=True)
    assert isinstance(router, APIRouter)
    assert hasattr(router, 'auth_required')
    assert router.auth_required is True

def test_tausestack_router_passes_standard_args():
    """Test TauseStackRouter passes standard APIRouter arguments."""
    router = TauseStackRouter(prefix="/api/v1", tags=["test"], auth_required=True)
    assert router.prefix == "/api/v1"
    assert router.tags == ["test"]
    assert router.auth_required is True

# --- Tests for Dynamic Router Loading ---

@pytest.fixture
def routers_dir(tmp_path):
    d = tmp_path / "routers"
    d.mkdir()
    # Router using the new TauseStackRouter class
    (d / "router1.py").write_text(
        "from tausestack.framework.routing import TauseStackRouter\n"
        "router = TauseStackRouter(prefix='/r1')"
    )
    # A standard APIRouter
    (d / "router2.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(prefix='/r2')"
    )
    # A file without a router attribute
    (d / "utils.py").write_text("def helper(): return 1")
    # An empty __init__.py
    (d / "__init__.py").touch()
    return str(d)

def test_dynamic_router_loading(app_for_router_loading, routers_dir):
    """Test that routers are loaded dynamically from a directory."""
    loaded_modules = load_routers_from_directory(app_for_router_loading, routers_dir)
    assert sorted(loaded_modules) == ["router1", "router2"]

def test_dynamic_router_loading_with_non_existent_dir(app_for_router_loading):
    """Test loading from a non-existent directory returns an empty list and doesn't crash."""
    loaded_modules = load_routers_from_directory(app_for_router_loading, "/non/existent/path")
    assert loaded_modules == []

def test_dynamic_router_loading_with_broken_file(app_for_router_loading, tmp_path, capsys):
    """Test that a broken Python file in the directory doesn't crash the loader."""
    d = tmp_path / "routers"
    d.mkdir()
    (d / "broken_route.py").write_text("import this_is_a_syntax_error")
    
    loaded_modules = load_routers_from_directory(app_for_router_loading, str(d))
    assert loaded_modules == []
    captured = capsys.readouterr()
    assert "Error loading router from 'broken_route.py'" in captured.out

# --- Tests for TauseStackRoute Authentication Logic ---

@pytest.fixture
def client_for_route_auth_tests():
    """Fixture to create a FastAPI app and client for testing route-level auth."""
    app = FastAPI(route_class=TauseStackRoute)

    # Public router - no authentication required
    public_router = TauseStackRouter(prefix="/public_rt", auth_required=False)
    @public_router.get("/resource")
    def get_public_resource():
        return {"message": "This is a public resource."}

    # Protected router - authentication required
    protected_router = TauseStackRouter(prefix="/protected_rt", auth_required=True)
    @protected_router.get("/resource")
    def get_protected_resource():
        return {"message": "This is a protected resource."}

    app.include_router(public_router)
    app.include_router(protected_router)
    
    return TestClient(app)

def test_access_public_route_via_tausestackroute(client_for_route_auth_tests):
    """Accessing a public route (auth_required=False) should always be allowed."""
    response = client_for_route_auth_tests.get("/public_rt/resource")
    assert response.status_code == 200
    assert response.json() == {"message": "This is a public resource."}

def test_access_protected_route_via_tausestackroute_without_auth_header(client_for_route_auth_tests):
    """Accessing a protected route (auth_required=True) without the auth header should be denied."""
    response = client_for_route_auth_tests.get("/protected_rt/resource")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_access_protected_route_via_tausestackroute_with_auth_header(client_for_route_auth_tests):
    """Accessing a protected route (auth_required=True) with the auth header should be allowed."""
    headers = {"X-Authenticated-User": "test-user"}
    response = client_for_route_auth_tests.get("/protected_rt/resource", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "This is a protected resource."}
