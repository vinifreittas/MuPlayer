import typer

from muplayer.infrastructure.system import check_engines, get_detected_os, install_engine

app = typer.Typer()


@app.command("setup")
def setup_cmd() -> None:
    """Run the setup wizard to install mpv/vlc players."""
    typer.secho("\n=== MuPlayer Setup Wizard ===\n", fg="cyan", bold=True)

    engines = check_engines()

    if path := engines["mpv"]:
        typer.secho(f"✓ Found 'mpv' engine at: {path}", fg="green")
    if path := engines["vlc"]:
        typer.secho(f"✓ Found 'vlc' engine at: {path}", fg="green")

    if engines["mpv"] or engines["vlc"]:
        typer.secho("\nSystem is fully configured! You are ready to go.", fg="green")
        if not typer.confirm("Do you want to run the installer setup anyway?", default=False):
            return

    typer.echo(f"\nDetected OS: {get_detected_os()}")

    def _validate_engine_choice(val: str) -> str:
        choice = val.strip().lower()
        if choice not in ("mpv", "vlc"):
            raise typer.BadParameter("Engine must be 'mpv' or 'vlc'.")
        return choice

    choice = typer.prompt(
        "Which engine would you like to set up? (mpv/vlc)",
        default="mpv",
        value_proc=_validate_engine_choice,
    )

    if typer.confirm(f"Would you like me to install {choice.upper()} now?"):
        success, message = install_engine(choice)
        if success:
            typer.secho(message, fg="green")
        else:
            typer.secho(message, fg="red" if "failed" in message.lower() or "error" in message.lower() else "yellow")
