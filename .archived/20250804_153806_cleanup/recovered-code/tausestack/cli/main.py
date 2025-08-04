import typer
from typing_extensions import Annotated

from tausestack import __version__ as tausestack_version
from .commands import init_cmd, run as run_cmd, deploy as deploy_cmd, framework_cmd

app = typer.Typer(
    name="tausestack",
    help="TauseStack CLI - Herramientas para gestionar tus proyectos TauseStack.",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="markdown"
)

# Registra los comandos de subdirectorios
app.add_typer(init_cmd.app, name="init", help="Inicializa un nuevo proyecto TauseStack.")
app.add_typer(run_cmd.app, name="run", help="Ejecuta la aplicación TauseStack o tareas relacionadas.")
app.add_typer(deploy_cmd.app, name="deploy", help="Despliega tu aplicación TauseStack.")
app.add_typer(framework_cmd.app, name="framework", help="Gestiona la aplicación del framework TauseStack.")


def version_callback(value: bool):
    if value:
        print(f"TauseStack CLI Version: {tausestack_version}")
        raise typer.Exit()

@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Mostrar la versión del TauseStack CLI y salir."
        )
    ] = False,
):
    """
    TauseStack CLI
    """
    # Este callback se ejecuta antes de cualquier comando
    # Se puede usar para configuraciones globales o checks
    pass

if __name__ == "__main__":
    app()
