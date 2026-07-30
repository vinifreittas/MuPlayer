import platform
import shutil
import subprocess

import typer

from muplayer.cli.utils import check_engines

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

    system = platform.system()
    typer.echo(f"\nDetected OS: {system}")

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
                result = subprocess.run(cmd, check=False)
                if result.returncode != 0:
                    typer.secho(
                        f"Command failed: {' '.join(cmd)}\nAborting installation.",
                        fg="red",
                    )
                    return
            typer.secho(f"✓ {choice.upper()} successfully installed!", fg="green")
        except subprocess.CalledProcessError:
            typer.secho("Package manager installation failed. Please run the commands manually.", fg="red")
