import typer

from muplayer.infrastructure.i18n import t
from muplayer.infrastructure.system import (
    check_for_updates,
    get_version,
    is_running_in_venv,
    perform_update,
)

app = typer.Typer()


@app.command("update")
def update_cmd() -> None:
    """Update the program to the latest version."""
    typer.echo("Checking for the latest version on GitHub...")
    current_ver = get_version()

    if "dev" in current_ver:
        typer.secho("You are running a local development version. Update skipped.", fg="yellow")
        return

    if not is_running_in_venv():
        typer.secho(t("update_outside_venv"), fg="yellow")
        if not typer.confirm("Continue anyway?", default=False):
            raise typer.Exit()

    is_newer, latest_tag, error = check_for_updates(current_ver)

    if error:
        typer.secho(error, fg="red")
        raise typer.Exit(code=1)

    if not is_newer:
        typer.secho(f"You are already up to date! (v{current_ver})", fg="green")
        return

    typer.echo(f"A new version is available: v{latest_tag} (Current: v{current_ver})")
    if not typer.confirm("Would you like to update now?"):
        typer.echo("Update aborted.")
        return

    typer.echo("Updating MuPlayer...")
    success, message = perform_update()
    if success:
        typer.secho(message, fg="green")
    else:
        typer.secho(message, fg="red")
