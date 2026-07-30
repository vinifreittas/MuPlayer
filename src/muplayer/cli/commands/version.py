import typer

from muplayer.cli.utils import get_version

app = typer.Typer()


@app.command("version")
def version_cmd() -> None:
    """Show the current program version."""
    typer.echo(f"MuPlayer {get_version()}")
