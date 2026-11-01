import typer

from muplayer.infrastructure.i18n import t
from muplayer.infrastructure.system import (
    check_for_updates,
    is_running_in_venv,
    perform_update,
)

app = typer.Typer()


@app.command("update")
def update_cmd() -> None:
    """Update the program to the latest version from GitHub."""
    typer.echo("Checking for the latest version on GitHub...")

    if not is_running_in_venv():
        typer.secho(t("update_outside_venv"), fg="yellow")
        if not typer.confirm("Continue anyway?", default=False):
            raise typer.Exit()

    is_update_available, installed_sha, latest_sha, error = check_for_updates()

    if error:
        typer.secho(error, fg="red")
        raise typer.Exit(code=1)

    installed_short = installed_sha[:7] if installed_sha else "unknown"
    latest_short = latest_sha[:7] if latest_sha else "unknown"

    if not is_update_available:
        typer.secho(f"You are already up to date! ({installed_short})", fg="green")
        return

    typer.echo(f"A new commit is available: {latest_short} (Current: {installed_short})")
    if not typer.confirm("Would you like to update now?"):
        typer.echo("Update aborted.")
        return

    typer.echo("Updating MuPlayer...")
    success, message = perform_update()
    if success:
        typer.secho(message, fg="green")
    else:
        typer.secho(message, fg="red")
