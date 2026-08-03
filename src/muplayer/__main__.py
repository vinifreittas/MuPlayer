import sys

import typer

from muplayer.interface.cli.commands import register_commands

# --- Instância Principal do CLI ---
cli = typer.Typer(
    name="muplayer",
    help="MuPlayer - A lightweight music app for terminal.",
    no_args_is_help=False,
    add_completion=False,
)

register_commands(cli)


# --- Helper Functions (Pre-flight Checks) ---


def _resolve_engine(engines: dict) -> str:
    """Retorna a engine disponível (dando preferência ao mpv)."""
    return "mpv" if engines.get("mpv") else "vlc"


def _validate_environment() -> dict:
    """Executa verificações prévias de dependências e suporte a terminal."""
    from muplayer.interface.cli.utils import check_engines, check_terminal_support

    engines = check_engines()
    if not engines.get("mpv") and not engines.get("vlc"):
        typer.secho(
            "\nError: Neither 'mpv' nor 'vlc' library was found on your system.\n"
            "MuPlayer needs one of these engines to play music.\n\n"
            "Please run: muplayer setup",
            fg="red",
            bold=True,
            err=True,
        )
        raise typer.Exit(code=1)

    is_terminal_ok, terminal_error = check_terminal_support()
    if not is_terminal_ok:
        typer.secho(
            f"\nError: Terminal environment is not supported for Textual TUI.\n"
            f"Reason: {terminal_error}\n\n"
            "Please run MuPlayer inside a modern interactive terminal emulator.",
            fg="red",
            bold=True,
            err=True,
        )
        raise typer.Exit(code=1)

    return engines


# --- Callback / Entrypoint CLI ---


@cli.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force start, bypassing any internal checks.",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug logging mode.",
    ),
) -> None:
    """Default action when muplayer is executed without subcommands."""
    if ctx.invoked_subcommand is None:
        from muplayer.infrastructure.logging import setup_logging
        from muplayer.interface.tui.app import MuPlayer

        setup_logging(debug)

        if not force:
            engines = _validate_environment()

        player_engine = _resolve_engine(engines)

        try:
            player = MuPlayer(player_engine=player_engine)
            player.run()
        except KeyboardInterrupt:
            typer.secho("\nMuPlayer session terminated by user.", fg="yellow")
            sys.exit(0)
        except Exception as e:
            typer.secho(f"\nFatal error starting MuPlayer: {e}", fg="red", err=True)
            raise typer.Exit(code=1) from None


if __name__ == "__main__":
    cli()
