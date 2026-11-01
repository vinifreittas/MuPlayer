import typer

from muplayer.infrastructure.system import check_engines, detect_js_runtime, install_defaults

app = typer.Typer()


@app.command("setup")
def setup_cmd() -> None:
    """Run the setup wizard to install mpv/vlc players and verify system dependencies."""
    typer.secho("\n=== MuPlayer Setup Wizard ===\n", fg="cyan", bold=True)

    engines = check_engines()
    js_runtime = detect_js_runtime()

    has_audio = bool(engines["mpv"] or engines["vlc"])
    has_js = js_runtime is not None

    if has_audio:
        typer.secho("✓ Audio engine (libmpv) found.", fg="green")
    else:
        typer.secho("✗ Audio engine (libmpv) not found.", fg="yellow")

    if has_js:
        typer.secho("✓ JavaScript runtime (quickjs) found.", fg="green")
    else:
        typer.secho("✗ JavaScript runtime (quickjs) not found.", fg="yellow")

    if has_audio and has_js:
        typer.secho("\nSystem is fully configured! Nothing to install.", fg="green")
        return

    if not typer.confirm("\nDownload and install missing dependencies from GitHub?", default=True):
        return

    for _asset_name, success, message in install_defaults():
        typer.secho(message, fg="green" if success else "red")
