import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

# Asegúrate de que 'app' es tu instancia principal de Typer en cli/main.py
from tausestack.cli.main import app

runner = CliRunner()

@pytest.fixture
def valid_project_dir(tmp_path: Path):
    """Crea un directorio de proyecto TauseStack simulado y cambia el CWD a él."""
    project_dir = tmp_path / "test_valid_project"
    project_dir.mkdir()
    (project_dir / "app").mkdir()
    (project_dir / "app" / "main.py").touch()  # Archivo que el comando run busca
    (project_dir / "pyproject.toml").touch() # Otro archivo que el comando run busca
    
    original_cwd = Path.cwd()
    os.chdir(project_dir) # El comando 'run dev' espera ejecutarse desde la raíz del proyecto
    yield project_dir
    os.chdir(original_cwd) # Restaura el CWD

@pytest.fixture
def invalid_project_dir(tmp_path: Path):
    """Crea un directorio que NO es un proyecto TauseStack y cambia el CWD a él."""
    non_project_dir = tmp_path / "test_invalid_project"
    non_project_dir.mkdir()
    
    original_cwd = Path.cwd()
    os.chdir(non_project_dir)
    yield non_project_dir
    os.chdir(original_cwd)

# El patch debe apuntar a 'os.execvp' donde se usa, es decir, en el módulo 'run.py'
@patch("tausestack.cli.commands.run.os.execvp")
def test_run_dev_default_args(mock_execvp: MagicMock, valid_project_dir: Path):
    """Prueba 'tausestack run dev' con argumentos por defecto."""
    result = runner.invoke(app, ["run", "dev"])
    
    assert result.exit_code == 0, f"Salida inesperada: {result.stdout}"
    
    mock_execvp.assert_called_once_with(
        "uvicorn", # El primer argumento de execvp es el comando
        ["uvicorn", "app.main:app", "--host=127.0.0.1", "--port=8000", "--reload"] # La lista completa de args
    )

@patch("tausestack.cli.commands.run.os.execvp")
def test_run_dev_custom_args(mock_execvp: MagicMock, valid_project_dir: Path):
    """Prueba 'tausestack run dev' con host, puerto y --no-reload personalizados."""
    result = runner.invoke(app, ["run", "dev", "--host", "0.0.0.0", "--port", "9000", "--no-reload"])
    
    assert result.exit_code == 0, f"Salida inesperada: {result.stdout}"
    mock_execvp.assert_called_once_with(
        "uvicorn",
        ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=9000"] # Sin --reload
    )

def test_run_dev_invalid_directory(invalid_project_dir: Path):
    """Prueba 'tausestack run dev' cuando se ejecuta fuera de un directorio de proyecto válido."""
    result = runner.invoke(app, ["run", "dev"])
    
    assert result.exit_code == 1
    assert "Error: No parece ser un directorio de proyecto TauseStack válido." in result.stdout

@patch("tausestack.cli.commands.run.os.execvp", side_effect=FileNotFoundError("uvicorn no encontrado"))
def test_run_dev_uvicorn_not_found(mock_execvp: MagicMock, valid_project_dir: Path):
    """Prueba 'tausestack run dev' cuando uvicorn no está instalado o no está en el PATH."""
    result = runner.invoke(app, ["run", "dev"])
    
    assert result.exit_code == 1
    assert "Error: Uvicorn no encontrado." in result.stdout
    mock_execvp.assert_called_once() # Verifica que se intentó llamar a execvp

@patch("tausestack.cli.commands.run.os.execvp", side_effect=Exception("Error genérico de execvp"))
def test_run_dev_generic_execvp_error(mock_execvp: MagicMock, valid_project_dir: Path):
    """Prueba 'tausestack run dev' cuando os.execvp lanza una excepción genérica."""
    result = runner.invoke(app, ["run", "dev"])
    
    assert result.exit_code == 1
    assert "Error inesperado al intentar ejecutar uvicorn: Error genérico de execvp" in result.stdout
    mock_execvp.assert_called_once()
