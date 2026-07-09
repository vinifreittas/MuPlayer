import typer

from muplayer import MuPlayer

# Initialize the Typer app
app = typer.Typer(
    name="muplayer",
    help="MuPlayer - A modern music player command-line interface.",
    no_args_is_help=False,  # We want to run the player if no args are given, not show help
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Default action when muplayer is executed without subcommands.
    """
    if ctx.invoked_subcommand is None:
        player = MuPlayer()
        player.run()


@app.command()
def version():
    """
    Show the program version.
    """
    typer.echo("MuPlayer 0.0.1")


@app.command()
def update():
    """
    Update the program to the latest version.
    """
    typer.echo("Updating MuPlayer...")


@app.command()
def setup():
    """
    Run the setup wizard.
    """
    typer.echo("Running setup wizard...")


if __name__ == "__main__":
    app()
