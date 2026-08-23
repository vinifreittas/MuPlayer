import typer

from muplayer.interface.cli.commands import register_commands

# ----- Principal CLI Instance -----

cli = typer.Typer(
    name="muplayer",
    help="MuPlayer - A lightweight music app for terminal.",
    no_args_is_help=False,
    add_completion=False,
)

register_commands(cli)


# ----- Callback / CLI Entrypoint -----


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
        from muplayer.application.bootstrap import run_app

        run_app(debug=debug, force=force)
