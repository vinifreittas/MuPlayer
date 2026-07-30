import logging
import sys

import typer

from muplayer.cli.commands.doctor import app as doctor_app
from muplayer.cli.commands.setup import app as setup_app
from muplayer.cli.commands.update import app as update_app
from muplayer.cli.commands.version import app as version_app

cli = typer.Typer(
    name="muplayer",
    help="MuPlayer - A lightweight music app for terminal.",
    no_args_is_help=False,
    add_completion=False,
)

# Unifica os subcomandos ao app principal
cli.add_typer(version_app)
cli.add_typer(doctor_app)
cli.add_typer(setup_app)
cli.add_typer(update_app)


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
        from muplayer.app import MuPlayer
        from muplayer.cli.utils import check_engines, check_terminal_support

        if debug:
            logging.getLogger().setLevel(logging.DEBUG)

        if not force:
            engines = check_engines()
            if not engines["mpv"] and not engines["vlc"]:
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

            player_engine = "mpv" if engines["mpv"] else "vlc"
        else:
            engines = check_engines()
            player_engine = "mpv" if engines["mpv"] else "vlc"

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
