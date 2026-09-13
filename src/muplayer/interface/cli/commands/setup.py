import typer

from muplayer.infrastructure.system import check_engines, detect_js_runtime, get_detected_os, install_engine

app = typer.Typer()


@app.command("setup")
def setup_cmd() -> None:
    """Run the setup wizard to install mpv/vlc players and verify system dependencies."""
    typer.secho("\n=== MuPlayer Setup Wizard ===\n", fg="cyan", bold=True)

    engines = check_engines()

    if path := engines["mpv"]:
        typer.secho(f"✓ Found 'mpv' audio engine at: {path}", fg="green")
    if path := engines["vlc"]:
        typer.secho(f"✓ Found 'vlc' audio engine at: {path}", fg="green")

    js_runtime = detect_js_runtime()
    if js_runtime:
        runtime_name = next(iter(js_runtime.keys()))
        typer.secho(f"✓ Found JavaScript engine: '{runtime_name}'", fg="green")
    else:
        typer.secho(
            "✗ Warning: No JavaScript runtime (quickjs, node, deno, bun) was found on your system PATH.\n"
            "  MuPlayer needs a JS runtime for stream URL extraction. Please install QuickJS or Node.js.",
            fg="yellow",
        )

    if (engines["mpv"] or engines["vlc"]) and js_runtime:
        typer.secho("\nSystem is fully configured! You are ready to go.", fg="green")
        if not typer.confirm("Do you want to run the installer setup anyway?", default=False):
            return

    typer.echo(f"\nDetected OS: {get_detected_os()}")

    has_audio = bool(engines["mpv"] or engines["vlc"])

    if not has_audio or typer.confirm(
        "Would you like to install the standard MPV audio engine?", default=not has_audio
    ):
        success, message = install_engine("mpv")
        if success:
            typer.secho(message, fg="green")
        else:
            typer.secho(message, fg="red" if "failed" in message.lower() or "error" in message.lower() else "yellow")

    if not js_runtime or typer.confirm(
        "Would you like to install the QuickJS JavaScript engine?", default=not js_runtime
    ):
        success, message = install_engine("quickjs")
        if success:
            typer.secho(message, fg="green")
        else:
            typer.secho(message, fg="red" if "failed" in message.lower() or "error" in message.lower() else "yellow")
