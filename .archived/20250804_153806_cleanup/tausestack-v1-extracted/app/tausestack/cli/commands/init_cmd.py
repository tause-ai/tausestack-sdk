import typer
import os
import shutil
import subprocess
from pathlib import Path
from typing_extensions import Annotated

app = typer.Typer(name="init", help="Inicializa un nuevo proyecto TauseStack.", no_args_is_help=True)

@app.command(name="project", help="Crea la estructura de un nuevo proyecto TauseStack.")
def init_project(
    project_name: Annotated[str, typer.Argument(help="El nombre del proyecto (y del directorio a crear).")],
    git: Annotated[bool, typer.Option("--git/--no-git", help="Inicializar un nuevo repositorio Git.")] = True,
    create_env_file: Annotated[bool, typer.Option("--env/--no-env", help="Crear un archivo .env a partir de .env.example.")] = True
):
    """
    Crea un nuevo proyecto TauseStack con la estructura de directorios y archivos base.
    """
    project_path = Path(project_name)

    if project_path.exists():
        typer.secho(f"Error: El directorio '{project_name}' ya existe.", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)

    try:
        typer.secho(f"Creando proyecto TauseStack '{project_name}'...", fg=typer.colors.CYAN)
        
        # Lógica para crear la estructura de directorios y archivos
        # Esto se implementará en el siguiente paso.
        project_path.mkdir(parents=True)
        (project_path / "app").mkdir()
        (project_path / "app" / "apis").mkdir()
        (project_path / "app" / "core").mkdir()
        (project_path / "app" / "models").mkdir()
        (project_path / "app" / "services").mkdir()
        (project_path / "tests").mkdir()

        # Crear archivos iniciales (ejemplos básicos)
        (project_path / "app" / "__init__.py").touch()
        (project_path / "app" / "apis" / "__init__.py").touch()
        (project_path / "app" / "core" / "__init__.py").touch()
        (project_path / "app" / "models" / "__init__.py").touch()
        (project_path / "app" / "services" / "__init__.py").touch()

        # main.py
        main_py_content = f"""
import os
from fastapi import FastAPI
from tausestack.framework.config import settings as tausestack_settings
from tausestack.framework.routing import load_routers_from_directory
# from app.core.config import my_app_settings # Descomentar si se usa config específica

APP_DIR = os.path.dirname(os.path.abspath(__file__))
APIS_DIR = os.path.join(APP_DIR, "apis")

app = FastAPI(
    title=getattr(my_app_settings if 'my_app_settings' in locals() else object(), 'APP_TITLE', tausestack_settings.APP_TITLE),
    version=getattr(my_app_settings if 'my_app_settings' in locals() else object(), 'APP_VERSION', tausestack_settings.APP_VERSION),
)

load_routers_from_directory(app, APIS_DIR)

@app.get("/")
async def root():
    return {{\"message\": f\"Bienvenido a {{app.title}} v{{app.version}}\"}}
"""
        (project_path / "app" / "main.py").write_text(main_py_content.strip())

        # .env.example
        env_example_content = """
# Variables de entorno para TauseStack Framework
# TAUSESTACK_LOG_LEVEL=INFO
# TAUSESTACK_FIREBASE_SA_KEY_PATH=path/to/your/serviceAccountKey.json
# TAUSESTACK_DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname
# TAUSESTACK_STORAGE_BACKEND=local # o 's3'
# TAUSESTACK_LOCAL_STORAGE_PATH=./.tausestack_storage
# TAUSESTACK_S3_BUCKET_NAME=your-s3-bucket-name
# TAUSESTACK_SECRETS_BACKEND=env # o 'aws'
# TAUSESTACK_NOTIFY_BACKEND=local_file # o 'ses'
# TAUSESTACK_NOTIFY_LOCAL_FILE_PATH=./.tausestack_notifications
# TAUSESTACK_NOTIFY_SES_SOURCE_EMAIL=noreply@example.com

# Variables específicas de la aplicación (si las hay)
# MI_CONFIG_ESPECIFICA=valor
"""
        (project_path / ".env.example").write_text(env_example_content.strip())
        if create_env_file:
            (project_path / ".env").write_text("# Copia y renombra .env.example a .env y configura tus variables\n" + env_example_content.strip())

        # pyproject.toml (básico)
        pyproject_toml_content = f"""
[build-system]
requires = [\"hatchling\"]
build-backend = \"hatchling.build\"

[project]
name = \"{project_name}\"
version = \"0.1.0\"
description = \"Un nuevo proyecto TauseStack\"
requires-python = \">=3.8\"

dependencies = [
    \"fastapi>=0.104.1\",
    \"uvicorn[standard]>=0.22.0\",
    \"tausestack @ git+https://github.com/tause-ai/tausestack.git#egg=tausestack\" # O la versión publicada
]

[tool.hatch.build.targets.wheel]
packages = [\"app\"]
"""
        (project_path / "pyproject.toml").write_text(pyproject_toml_content.strip())

        # README.md
        readme_content = f"""
# {project_name.capitalize()}

Un nuevo proyecto generado con TauseStack.

## Para empezar

1.  Crea y activa un entorno virtual:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt # O pip install -e . si usas hatch
    ```
3.  Configura tus variables de entorno en `.env` (copia de `.env.example`).
4.  Ejecuta la aplicación:
    ```bash
    uvicorn app.main:app --reload
    ```
"""
        (project_path / "README.md").write_text(readme_content.strip())

        if git:
            try:
                typer.secho("Inicializando repositorio Git...", fg=typer.colors.CYAN)
                subprocess.run(["git", "init"], cwd=project_path, check=True, capture_output=True)
                subprocess.run(["git", "add", "."], cwd=project_path, check=True, capture_output=True)
                subprocess.run(["git", "commit", "-m", "Initial commit from TauseStack CLI"], cwd=project_path, check=True, capture_output=True)
                typer.secho("✓ Repositorio Git inicializado.", fg=typer.colors.GREEN)
            except (subprocess.CalledProcessError, FileNotFoundError) as git_error:
                typer.secho("Error al inicializar el repositorio Git.", fg=typer.colors.RED, bold=True)
                typer.secho("Por favor, asegúrate de que Git está instalado y en tu PATH.", fg=typer.colors.YELLOW)
                typer.secho(f"Detalle del error: {git_error}", fg=typer.colors.YELLOW, err=True)
                # No detenemos la creación del proyecto, solo advertimos.
        
        typer.secho(f"Proyecto '{project_name}' creado exitosamente en ./{project_name}", fg=typer.colors.GREEN, bold=True)
        typer.secho("Siguientes pasos:", fg=typer.colors.YELLOW)
        typer.echo(f"  1. cd {project_name}")
        typer.echo("  2. Crea y activa un entorno virtual (ej. python -m venv .venv && source .venv/bin/activate)")
        typer.echo("  3. Instala las dependencias (ej. pip install -e .)")
        typer.echo("  4. Configura tu archivo .env")
        typer.echo("  5. Ejecuta: uvicorn app.main:app --reload")

    except Exception as e:
        typer.secho(f"Error al crear el proyecto: {e}", fg=typer.colors.RED, bold=True)
        # Considerar limpieza si falla a mitad de camino
        if project_path.exists():
            shutil.rmtree(project_path)
            typer.secho(f"Directorio del proyecto '{project_name}' eliminado debido al error.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
