import pytest
from typer.testing import CliRunner
from pathlib import Path
import shutil
import os
from unittest.mock import patch

from tausestack.cli.main import app # app es la instancia de Typer

runner = CliRunner()

@pytest.fixture
def temp_test_dir(tmp_path: Path) -> Path:
    """Crea un directorio temporal para ejecutar el CLI y lo limpia después."""
    test_dir = tmp_path / "cli_execution_test"
    test_dir.mkdir()
    original_cwd = Path.cwd()
    os.chdir(test_dir) # Cambia el CWD para que el proyecto se cree dentro de tmp_path
    yield test_dir
    os.chdir(original_cwd) # Restaura el CWD original
    # shutil.rmtree(test_dir) # tmp_path se encarga de la limpieza

def test_init_project_creates_structure(temp_test_dir: Path):
    """Test that 'tausestack init project <name>' creates the basic structure."""
    project_name = "my_cli_test_app"
    
    # Invoca el comando: tausestack init project my_cli_test_app
    # Asegúrate de que app se importa desde tausestack.cli.main
    result = runner.invoke(app, ["init", "project", project_name])

    assert result.exit_code == 0, f"CLI command failed: {result.stdout}"
    assert f"Proyecto '{project_name}' creado exitosamente" in result.stdout

    project_path = temp_test_dir / project_name
    assert project_path.is_dir(), f"Project directory '{project_name}' was not created."

    # Verificar directorios clave
    assert (project_path / "app").is_dir()
    assert (project_path / "app" / "apis").is_dir()
    assert (project_path / "app" / "core").is_dir()
    assert (project_path / "app" / "models").is_dir()
    assert (project_path / "app" / "services").is_dir()
    assert (project_path / "tests").is_dir()

    # Verificar archivos clave
    assert (project_path / "app" / "main.py").is_file()
    assert (project_path / "pyproject.toml").is_file()
    assert (project_path / ".env.example").is_file()
    assert (project_path / ".env").is_file()
    assert (project_path / "README.md").is_file()

    # Verificar que el repo git se inicializa por defecto
    assert (project_path / ".git").is_dir(), "Git repository was not initialized by default."

def test_init_project_with_no_git(temp_test_dir: Path):
    """Test that 'tausestack init project --no-git' skips git initialization."""
    project_name = "my_no_git_app"
    result = runner.invoke(app, ["init", "project", project_name, "--no-git"])

    assert result.exit_code == 0
    project_path = temp_test_dir / project_name
    assert project_path.is_dir()
    assert not (project_path / ".git").exists(), "Git repository should not be initialized with --no-git flag."

def test_init_project_with_no_env_file(temp_test_dir: Path):
    """Test that 'tausestack init project --no-env' skips .env file creation."""
    project_name = "my_no_env_app"
    result = runner.invoke(app, ["init", "project", project_name, "--no-env"])

    assert result.exit_code == 0, f"CLI command failed: {result.stdout}"
    project_path = temp_test_dir / project_name
    assert project_path.is_dir()
    assert not (project_path / ".env").exists(), ".env file should not be created with --no-env flag."
    assert (project_path / ".env.example").is_file(), ".env.example file should still be created."

def test_init_project_git_failure_warning(temp_test_dir: Path):
    """Test that a git failure shows a warning but doesn't stop project creation."""
    project_name = "my_git_fail_app"
    
    with patch("subprocess.run", side_effect=FileNotFoundError("git command not found")):
        result = runner.invoke(app, ["init", "project", project_name]) # --git es el default

    assert result.exit_code == 0, "Project creation should succeed even if git fails."
    assert "Error al inicializar el repositorio Git." in result.stdout
    assert "Por favor, asegúrate de que Git está instalado" in result.stdout

    project_path = temp_test_dir / project_name
    assert project_path.is_dir(), "Project directory should still be created after git failure."
    assert not (project_path / ".git").exists(), "Git directory should not exist after git failure."

def test_init_project_existing_directory(temp_test_dir: Path):
    """Test that 'tausestack init project <name>' fails if directory exists."""
    project_name = "my_existing_app"
    (temp_test_dir / project_name).mkdir() # Crear el directorio de antemano

    result = runner.invoke(app, ["init", "project", project_name])

    assert result.exit_code == 1, "CLI command should fail for existing directory."
    assert f"Error: El directorio '{project_name}' ya existe." in result.stdout
