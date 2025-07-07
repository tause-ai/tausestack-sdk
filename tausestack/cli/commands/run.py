# Comandos CLI para ejecutar la aplicación TauseStack

import typer
import subprocess
from pathlib import Path
import os

app = typer.Typer()

@app.command("dev")
def run_dev(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="El host en el que escuchar."),
    port: int = typer.Option(8000, "--port", "-p", help="El puerto en el que escuchar."),
    reload: bool = typer.Option(True, "--reload/--no-reload", help="Activar/desactivar recarga automática.")
):
    """
    Ejecuta el servidor de desarrollo Uvicorn para la aplicación TauseStack.

    Busca 'app/main.py' en el directorio actual.
    """
    project_root = Path.cwd()
    app_main_path = project_root / "app" / "main.py"
    pyproject_path = project_root / "pyproject.toml"

    if not app_main_path.exists() or not pyproject_path.exists():
        typer.secho(
            "Error: No parece ser un directorio de proyecto TauseStack válido.",
            fg=typer.colors.RED,
            err=True
        )
        typer.secho(
            f"Asegúrate de que '{app_main_path.relative_to(project_root)}' y '{pyproject_path.relative_to(project_root)}' existan.",
            fg=typer.colors.RED,
            err=True
        )
        raise typer.Exit(code=1)

    command = [
        "uvicorn",
        "app.main:app",
        f"--host={host}",
        f"--port={port}",
    ]
    if reload:
        command.append("--reload")

    typer.secho(f"Iniciando servidor de desarrollo con el comando: {' '.join(command)}", fg=typer.colors.CYAN)
    
    try:
        # Usamos os.execvp para reemplazar el proceso actual con uvicorn.
        # Esto permite que uvicorn maneje correctamente las señales (ej. Ctrl+C).
        # Nota: esto significa que cualquier código después de os.execvp no se ejecutará.
        os.execvp(command[0], command)
    except FileNotFoundError:
        typer.secho(
            "Error: Uvicorn no encontrado. Asegúrate de que esté instalado y en tu PATH.",
            fg=typer.colors.RED,
            err=True
        )
        typer.secho(
            "Puedes instalarlo con: pip install uvicorn[standard]",
            fg=typer.colors.YELLOW,
            err=True
        )
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Error inesperado al intentar ejecutar uvicorn: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
