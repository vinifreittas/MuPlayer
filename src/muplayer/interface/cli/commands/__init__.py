import typer

from muplayer.interface.cli.commands.doctor import app as doctor_app
from muplayer.interface.cli.commands.setup import app as setup_app
from muplayer.interface.cli.commands.update import app as update_app
from muplayer.interface.cli.commands.version import app as version_app


def register_commands(cli: typer.Typer) -> None:
    """Registra todos os subcomandos do Typer no CLI principal."""
    cli.add_typer(version_app)
    cli.add_typer(doctor_app)
    cli.add_typer(setup_app)
    cli.add_typer(update_app)
