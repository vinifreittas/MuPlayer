import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

import typer

from muplayer import MuPlayer

# Initialize the Typer app
app = typer.Typer(
    name="muplayer",
    help="MuPlayer - A modern music player command-line interface.",
    no_args_is_help=False,  # Run the player if no args are given, rather than showing help
    add_completion=False,
)

# Configuration Constants
GITHUB_REPO = "vinifreittas/MuPlayer"
USER_AGENT = "MuPlayerUpdateChecker/1.0"


def get_version() -> str:
    """Dynamically fetches the installed package version."""
    try:
        return importlib.metadata.version("muplayer")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.1 (local/dev)"


def check_engines() -> dict[str, str | None]:
    """Checks if mpv or vlc are installed on the system PATH."""
    return {"mpv": shutil.which("mpv"), "vlc": shutil.which("vlc")}


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Default action when muplayer is executed without subcommands."""
    if ctx.invoked_subcommand is None:
        engines = check_engines()
        if not engines["mpv"] and not engines["vlc"]:
            typer.secho(
                "\nError: Neither 'mpv' nor 'vlc' was found on your system PATH.\n"
                "MuPlayer needs one of these engines to play music.\n\n"
                "Please run: muplayer setup",
                fg="red",
                bold=True,
                err=True,
            )
            raise typer.Exit(code=1)

        # Proceed to run the player if at least one backend exists
        player = MuPlayer()
        player.run()


@app.command()
def version() -> None:
    """Show the current program version."""
    typer.echo(f"MuPlayer {get_version()}")


@app.command()
def update() -> None:
    """Update the program to the latest version."""
    typer.echo("Checking for the latest version on GitHub...")
    current_ver = get_version()

    if "dev" in current_ver:
        typer.secho("You are running a local development version. Update skipped.", fg="yellow")
        return

    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            latest_ver = data["tag_name"].lstrip("v")
    except urllib.error.URLError as e:
        typer.secho(f"Network error: Could not check for updates ({e.reason}).", fg="red")
        raise typer.Exit(code=1) from None
    except json.JSONDecodeError:
        typer.secho("Error: Failed to parse update response from GitHub.", fg="red")
        raise typer.Exit(code=1) from None
    except Exception as e:
        typer.secho(f"An unexpected error occurred: {e}", fg="red")
        raise typer.Exit(code=1) from None

    if latest_ver == current_ver:
        typer.secho(f"You are already up to date! (v{current_ver})", fg="green")
        return

    typer.echo(f"A new version is available: v{latest_ver} (Current: v{current_ver})")
    if not typer.confirm("Would you like to update now?"):
        typer.echo("Update aborted.")
        return

    typer.echo("Updating MuPlayer...")
    try:
        if shutil.which("uv"):
            typer.echo("Using 'uv tool' to upgrade from GitHub...")
            subprocess.run(["uv", "tool", "upgrade", "muplayer"], check=True)
        else:
            typer.echo("Using 'pip' to upgrade from GitHub...")
            git_url = f"git+https://github.com/{GITHUB_REPO}.git"
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", git_url], check=True)

        typer.secho("Successfully updated MuPlayer!", fg="green")
    except subprocess.CalledProcessError:
        typer.secho("Update failed. Please run the upgrade command manually.", fg="red")


@app.command()
def setup() -> None:
    """Run the setup wizard to install mpv/vlc engines."""
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

    system = platform.system()
    typer.echo(f"\nDetected OS: {system}")

    choice = typer.prompt(
        "Which engine would you like to set up?", type=str, default="mpv", choices=["mpv", "vlc"]
    ).lower()

    match system:
        case "Windows":
            _setup_windows(choice)
        case "Darwin":
            _setup_macos(choice)
        case "Linux":
            _setup_linux(choice)
        case _:
            typer.secho(
                f"Unsupported OS: {system}. Please download and install {choice.upper()} manually "
                "and add its directory to your PATH variable.",
                fg="yellow",
            )


# --- OS Specific Helper Functions ---


def _setup_windows(choice: str) -> None:
    typer.echo(f"\nSetting up {choice.upper()} for Windows...")

    if shutil.which("winget"):
        typer.echo("Using Windows Package Manager (winget)...")
        package_id = "xtse.mpv" if choice == "mpv" else "VideoLAN.VLC"
        try:
            subprocess.run(["winget", "install", package_id], check=True)
            typer.secho(
                f"✓ {choice.upper()} installed successfully! You may need to restart your terminal.", fg="green"
            )
        except subprocess.CalledProcessError:
            typer.secho("Installation via winget failed.", fg="red")
            _manual_windows_instructions(choice)
    else:
        _manual_windows_instructions(choice)


def _manual_windows_instructions(choice: str) -> None:
    typer.secho("\nPlease follow these manual steps:", fg="yellow")
    if choice == "mpv":
        typer.echo("1. Go to: https://mpv.io/installation/")
        typer.echo("2. Download the Windows build.")
        typer.echo("3. Extract the ZIP to a directory (e.g., C:\\tools\\mpv).")
        typer.echo("4. Add 'C:\\tools\\mpv' to your User PATH Environment Variables.")
    else:
        typer.echo("1. Download VLC from: https://www.videolan.org/vlc/")
        typer.echo("2. Complete the installer wizard.")
        typer.echo(
            "3. Add the installation path (typically C:\\Program Files\\VideoLAN\\VLC) to your Environment PATH."
        )


def _setup_macos(choice: str) -> None:
    typer.echo(f"\nSetting up {choice.upper()} for macOS...")

    if shutil.which("brew"):
        typer.echo("Using Homebrew to install...")
        cmd = ["brew", "install", "mpv"] if choice == "mpv" else ["brew", "install", "--cask", "vlc"]
        try:
            subprocess.run(cmd, check=True)
            typer.secho(f"✓ {choice.upper()} successfully installed via Homebrew!", fg="green")
        except subprocess.CalledProcessError:
            typer.secho("Homebrew installation failed.", fg="red")
    else:
        typer.secho("\nHomebrew ('brew') was not detected.", fg="yellow")
        if choice == "mpv":
            typer.echo("Please install Homebrew (https://brew.sh) first, then run: brew install mpv")
        else:
            typer.echo("Download and install VLC manually from: https://www.videolan.org/vlc/")


def _setup_linux(choice: str) -> None:
    typer.echo(f"\nSetting up {choice.upper()} for Linux...")

    commands: list[list[str]] = []
    if shutil.which("apt-get"):
        commands = [["sudo", "apt-get", "update"], ["sudo", "apt-get", "install", "-y", choice]]
    elif shutil.which("pacman"):
        commands = [["sudo", "pacman", "-S", "--noconfirm", choice]]
    elif shutil.which("dnf"):
        commands = [["sudo", "dnf", "install", "-y", choice]]

    if not commands:
        typer.secho(
            f"Could not identify package manager. Please use your system package manager to install {choice}.",
            fg="yellow",
        )
        return

    flat_command_str = " && ".join(" ".join(cmd) for cmd in commands)
    typer.echo(f"Suggested command: {flat_command_str}")

    if typer.confirm("Would you like me to execute these commands for you?"):
        try:
            for cmd in commands:
                subprocess.run(cmd, check=True)
            typer.secho(f"✓ {choice.upper()} successfully installed!", fg="green")
        except subprocess.CalledProcessError:
            typer.secho("Package manager installation failed. Please run the commands manually.", fg="red")


if __name__ == "__main__":
    app()
