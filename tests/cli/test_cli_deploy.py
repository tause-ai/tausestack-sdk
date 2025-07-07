import pytest
from typer.testing import CliRunner
from pathlib import Path
import os
import subprocess
from unittest.mock import patch, MagicMock

# Asegúrate de que 'app' es tu instancia principal de Typer en cli/main.py
from tausestack.cli.main import app

runner = CliRunner()

@pytest.fixture
def valid_project_dir(tmp_path: Path):
    """Crea un directorio de proyecto TauseStack simulado y cambia el CWD a él."""
    project_dir = tmp_path / "test_valid_project_for_deploy"
    project_dir.mkdir()
    (project_dir / "app").mkdir()
    (project_dir / "app" / "main.py").touch()
    (project_dir / "pyproject.toml").touch()
    
    original_cwd = Path.cwd()
    os.chdir(project_dir)
    yield project_dir
    os.chdir(original_cwd)

@pytest.fixture
def valid_project_with_dockerfile_dir(valid_project_dir: Path):
    """Añade un Dockerfile al directorio de proyecto válido."""
    (valid_project_dir / "Dockerfile").touch()
    yield valid_project_dir

@pytest.fixture
def invalid_project_dir(tmp_path: Path):
    """Crea un directorio que NO es un proyecto TauseStack y cambia el CWD a él."""
    non_project_dir = tmp_path / "test_invalid_project_for_deploy"
    non_project_dir.mkdir()
    
    original_cwd = Path.cwd()
    os.chdir(non_project_dir)
    yield non_project_dir
    os.chdir(original_cwd)

def test_deploy_target_in_valid_project(valid_project_dir: Path):
    """Prueba 'tausestack deploy target' en un proyecto válido sin Dockerfile."""
    result = runner.invoke(app, ["deploy", "target", "production"])
    
    assert result.exit_code == 0
    assert "Iniciando proceso de despliegue para el entorno: production" in result.stdout
    assert "✗ Dockerfile no encontrado" in result.stdout
    assert "Despliegue simulado a 'production' completado" in result.stdout

def test_deploy_target_in_valid_project_with_dockerfile(valid_project_with_dockerfile_dir: Path):
    """Prueba 'tausestack deploy target' en un proyecto válido con Dockerfile."""
    result = runner.invoke(app, ["deploy", "target", "staging"])
    
    assert result.exit_code == 0
    assert "Iniciando proceso de despliegue para el entorno: staging" in result.stdout
    assert "✓ Dockerfile encontrado" in result.stdout
    # Ahora debería sugerir el comando con tausestack o el nombre del proyecto
    project_name = valid_project_with_dockerfile_dir.name.lower().replace('_', '-')
    assert f"tausestack deploy target staging --build" in result.stdout
    assert f"docker build -t {project_name}:staging ." in result.stdout
    assert "Despliegue simulado a 'staging' completado" in result.stdout

def test_deploy_target_in_invalid_project(invalid_project_dir: Path):
    """Prueba 'tausestack deploy target' fuera de un directorio de proyecto válido."""
    result = runner.invoke(app, ["deploy", "target", "production"])
    
    assert result.exit_code == 1
    assert "Error: No parece ser un directorio de proyecto TauseStack válido." in result.stderr

def test_deploy_target_default_environment(valid_project_dir: Path):
    """Prueba 'tausestack deploy target' usando el entorno por defecto ('production')."""
    result = runner.invoke(app, ["deploy", "target"]) # No se especifica entorno
    
    assert result.exit_code == 0
    assert "Iniciando proceso de despliegue para el entorno: production" in result.stdout
    assert "Despliegue simulado a 'production' completado" in result.stdout


@patch("tausestack.cli.commands.deploy.subprocess.run")
def test_deploy_target_build_docker_success(mock_subprocess_run: MagicMock, valid_project_with_dockerfile_dir: Path):
    """Prueba 'tausestack deploy target --build' con Dockerfile y build exitoso."""
    mock_subprocess_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="Build successful", stderr="")
    project_name = valid_project_with_dockerfile_dir.name.lower().replace('_', '-')
    environment = "dev"

    result = runner.invoke(app, ["deploy", "target", environment, "--build"])

    assert result.exit_code == 0, result.stdout
    assert f"Intentando construir la imagen Docker: {project_name}:{environment}" in result.stdout
    mock_subprocess_run.assert_called_once_with(
        ["docker", "build", "-t", f"{project_name}:{environment}", "."],
        check=True,
        capture_output=True,
        text=True,
        cwd=valid_project_with_dockerfile_dir
    )
    assert f"Imagen Docker '{project_name}:{environment}' construida exitosamente." in result.stdout
    assert "Build successful" in result.stdout


@patch("tausestack.cli.commands.deploy.subprocess.run")
def test_deploy_target_build_docker_no_dockerfile(mock_subprocess_run: MagicMock, valid_project_dir: Path):
    """Prueba 'tausestack deploy target --build' sin Dockerfile."""
    result = runner.invoke(app, ["deploy", "target", "production", "--build"])

    assert result.exit_code == 0, result.stdout
    assert "✗ Dockerfile no encontrado" in result.stdout
    assert "La opción --build fue especificada, pero no se encontró un Dockerfile. Saltando construcción." in result.stdout
    mock_subprocess_run.assert_not_called()


@patch("tausestack.cli.commands.deploy.subprocess.run", side_effect=FileNotFoundError("docker not found"))
def test_deploy_target_build_docker_command_not_found(mock_subprocess_run: MagicMock, valid_project_with_dockerfile_dir: Path):
    """Prueba 'tausestack deploy target --build' cuando docker no está instalado."""
    result = runner.invoke(app, ["deploy", "target", "production", "--build"])

    assert result.exit_code == 1, result.stderr
    assert "Error: El comando 'docker' no fue encontrado." in result.stderr
    mock_subprocess_run.assert_called_once()


@patch("tausestack.cli.commands.deploy.subprocess.run")
def test_deploy_target_build_docker_build_fails(mock_subprocess_run: MagicMock, valid_project_with_dockerfile_dir: Path):
    """Prueba 'tausestack deploy target --build' cuando 'docker build' falla."""
    project_name = valid_project_with_dockerfile_dir.name.lower().replace('_', '-')
    environment = "prod"
    cmd_ran = ["docker", "build", "-t", f"{project_name}:{environment}", "."]
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd=cmd_ran, output="Build failed stdout", stderr="Build failed stderr"
    )

    result = runner.invoke(app, ["deploy", "target", environment, "--build"])

    assert result.exit_code == 1, result.stderr
    assert f"Error al construir la imagen Docker '{project_name}:{environment}'." in result.stderr
    assert "Comando: docker build -t" in result.stderr # Parte del comando
    assert "Código de retorno: 1" in result.stderr
    assert "Salida (stdout) del error:" in result.stdout
    assert "Build failed stdout" in result.stderr
    assert "Salida (stderr) del error:" in result.stdout
    assert "Build failed stderr" in result.stderr
    mock_subprocess_run.assert_called_once()
