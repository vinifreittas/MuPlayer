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
        "Would you like to configure/install an audio engine (mpv/vlc)?", default=not has_audio
    ):

        def _validate_engine_choice(val: str) -> str:
            choice = val.strip().lower()
            if choice not in ("mpv", "vlc"):
                raise typer.BadParameter("Engine must be 'mpv' or 'vlc'.")
            return choice

        choice = typer.prompt(
            "Which audio engine would you like to set up? (mpv/vlc)",
            default="mpv",
            value_proc=_validate_engine_choice,
        )

        if typer.confirm(f"Would you like me to install {choice.upper()} now?"):
            success, message = install_engine(choice)
            if success:
                typer.secho(message, fg="green")
            else:
                typer.secho(
                    message, fg="red" if "failed" in message.lower() or "error" in message.lower() else "yellow"
                )

    if not js_runtime or typer.confirm(
        "Would you like to install a JavaScript runtime (quickjs/node)?", default=not js_runtime
    ):

        def _validate_js_choice(val: str) -> str:
            choice = val.strip().lower()
            if choice not in ("quickjs", "node", "nodejs"):
                raise typer.BadParameter("JS engine choice must be 'quickjs' or 'node'.")
            return choice

        js_choice = typer.prompt(
            "Which JavaScript runtime would you like to set up? (quickjs/node)",
            default="quickjs",
            value_proc=_validate_js_choice,
        )

        if typer.confirm(f"Would you like me to install {js_choice.upper()} now?"):
            success, message = install_engine(js_choice)
            if success:
                typer.secho(message, fg="green")
            else:
                typer.secho(
                    message, fg="red" if "failed" in message.lower() or "error" in message.lower() else "yellow"
                )
