import typer
import uvicorn
from typing_extensions import Annotated

app = typer.Typer(
    name="framework",
    help="Gestiona la aplicación del framework TauseStack.",
    no_args_is_help=True
)

@app.command("run")
def run_framework(
    host: Annotated[str, typer.Option(help="El host en el que escuchar.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="El puerto en el que escuchar.")] = 8000,
    reload: Annotated[bool, typer.Option(help="Activar la recarga automática.")] = True,
):
    """Inicia el servidor de la aplicación del framework TauseStack."""
    typer.echo(f"Iniciando servidor en http://{host}:{port} con recarga {'activada' if reload else 'desactivada'}...")
    try:
        # Intentamos importar la app del framework dinámicamente para evitar 
        # problemas de importación circular o dependencias en el nivel superior del CLI.
        app_identifier = "tausestack.framework.main:app"
        if reload:
            uvicorn.run(app_identifier, host=host, port=port, reload=True, log_level="debug")
        else:
            # Si no hay recarga, podemos importar y pasar el objeto directamente
            from tausestack.framework.main import app as framework_app
            uvicorn.run(framework_app, host=host, port=port, reload=False)
    except ImportError:
        typer.secho(
            "Error: No se pudo importar la aplicación del framework. Asegúrate de que 'tausestack.framework.main' exista y sea accesible.", 
            fg=typer.colors.RED, 
            err=True
        )
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Error al iniciar el servidor: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
