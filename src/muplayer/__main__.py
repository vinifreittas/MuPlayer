import importlib.metadata
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

import typer
from rich.console import Console
from rich.table import Table

from muplayer import MuPlayer

# Initialize the Typer app
cli = typer.Typer(
    name="muplayer",
    help="MuPlayer - A lightweight music app for terminal.",
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


def get_engine_version(engine_name: str) -> str | None:
    """Helper to retrieve version string of installed engine."""
    binary = shutil.which(engine_name)
    if not binary:
        return None
    try:
        res = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        output = (res.stdout or res.stderr or "").strip()
        first_line = output.splitlines()[0] if output else "Installed"
        return first_line
    except Exception:
        return "Installed"


def check_terminal_support() -> tuple[bool, str | None]:
    """Checks if the terminal environment supports running the Textual TUI"""
    console = Console()

    if not sys.stdin.isatty():
        return False, "Standard input (stdin) is not attached to an interactive terminal (TTY)."

    if not console.is_terminal:
        return False, "Standard output (stdout) is not attached to an interactive terminal (TTY)."

    if console.is_dumb_terminal:
        return False, "Terminal is identified as 'dumb' and lacks ANSI escape sequence support."

    if console.color_system is None:
        return False, "Terminal environment does not support color rendering."

    return True, None


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
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)

        if not force:
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

        try:
            player = MuPlayer()
            player.run()
        except KeyboardInterrupt:
            typer.secho("\nMuPlayer session terminated by user.", fg="yellow")
            sys.exit(0)
        except Exception as e:
            typer.secho(f"\nFatal error starting MuPlayer: {e}", fg="red", err=True)
            raise typer.Exit(code=1) from None


@cli.command()
def version() -> None:
    """Show the current program version."""
    typer.echo(f"MuPlayer {get_version()}")


@cli.command()
def doctor() -> None:
    """Run system diagnostics and display environment details."""
    console = Console()
    console.print("\n[bold cyan]=== MuPlayer System Doctor ===[/bold cyan]\n")

    # Table 1: System Info
    sys_table = Table(title="System Information", show_header=True, header_style="bold magenta")
    sys_table.add_column("Property", style="cyan")
    sys_table.add_column("Value", style="green")

    sys_table.add_row("MuPlayer Version", get_version())
    sys_table.add_row("Python Version", sys.version.split()[0])
    sys_table.add_row("OS / Platform", f"{platform.system()} {platform.release()} ({platform.machine()})")
    sys_table.add_row("Executable Path", sys.executable)
    console.print(sys_table)
    console.print()

    # Table 2: Terminal Environment
    term_table = Table(title="Terminal Environment", show_header=True, header_style="bold magenta")
    term_table.add_column("Check", style="cyan")
    term_table.add_column("Status", style="bold")
    term_table.add_column("Details", style="dim")

    is_stdin_tty = sys.stdin.isatty()
    term_table.add_row(
        "Interactive Input (stdin)",
        "[green]PASS[/green]" if is_stdin_tty else "[red]FAIL[/red]",
        "Connected to TTY" if is_stdin_tty else "Not attached to interactive TTY",
    )

    is_stdout_tty = console.is_terminal
    term_table.add_row(
        "Terminal Output (stdout)",
        "[green]PASS[/green]" if is_stdout_tty else "[red]FAIL[/red]",
        "Connected to terminal" if is_stdout_tty else "Not attached to terminal",
    )

    is_dumb = console.is_dumb_terminal
    term_table.add_row(
        "Terminal Type",
        "[red]FAIL (Dumb)[/red]" if is_dumb else "[green]PASS[/green]",
        f"TERM={os.getenv('TERM', 'not set')}",
    )

    color_sys = console.color_system
    term_table.add_row(
        "Color Support",
        "[green]PASS[/green]" if color_sys else "[red]FAIL[/red]",
        f"Detected: {color_sys}" if color_sys else "No color support detected",
    )

    cols, lines = shutil.get_terminal_size()
    term_table.add_row(
        "Terminal Dimensions",
        "[green]INFO[/green]",
        f"{cols} columns x {lines} rows",
    )

    console.print(term_table)
    console.print()

    # Table 3: Audio Engines
    eng_table = Table(title="Audio Playback Engines", show_header=True, header_style="bold magenta")
    eng_table.add_column("Engine", style="cyan")
    eng_table.add_column("Installed", style="bold")
    eng_table.add_column("Version / Path", style="dim")

    engines = check_engines()
    for engine_name in ["mpv", "vlc"]:
        path = engines[engine_name]
        if path:
            version_info = get_engine_version(engine_name) or path
            eng_table.add_row(engine_name.upper(), "[green]YES[/green]", f"{version_info} ({path})")
        else:
            eng_table.add_row(engine_name.upper(), "[red]NO[/red]", "Not found on system PATH")

    console.print(eng_table)
    console.print()

    # Table 4: Paths & Data
    path_table = Table(title="Data & Storage Paths", show_header=True, header_style="bold magenta")
    path_table.add_column("Item", style="cyan")
    path_table.add_column("Path", style="dim")

    from muplayer.app import DATA_DIR

    path_table.add_row("Data Directory", str(DATA_DIR.resolve()))
    path_table.add_row("Config File", str((DATA_DIR / "config.json").resolve()))
    path_table.add_row("Database File", str((DATA_DIR / "app_data.db").resolve()))
    path_table.add_row("Logs Directory", str((DATA_DIR / "logs").resolve()))
    console.print(path_table)
    console.print()

    # Summary
    is_term_ok, term_err = check_terminal_support()
    has_engine = bool(engines["mpv"] or engines["vlc"])

    if is_term_ok and has_engine:
        console.print("[bold green]✓ Everything looks good! MuPlayer is ready to run.[/bold green]\n")
    else:
        console.print("[bold red]✗ System configuration issue detected:[/bold red]")
        if not has_engine:
            console.print("  - Missing audio engine ('mpv' or 'vlc'). Run: [cyan]muplayer setup[/cyan]")
        if not is_term_ok:
            console.print(f"  - Terminal issue: {term_err}")
        console.print()


@cli.command()
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

    git_url = f"git+https://github.com/{GITHUB_REPO}.git"
    try:
        if shutil.which("uv"):
            typer.echo("Using 'uv' to upgrade...")
            command = ["uv", "pip", "install", "--upgrade", "--python", sys.executable, git_url]
        else:
            typer.echo("Using 'pip' to upgrade...")
            command = [sys.executable, "-m", "pip", "install", "--upgrade", git_url]

        subprocess.run(command, check=True)
        typer.secho("Successfully updated MuPlayer!", fg="green")

    except subprocess.CalledProcessError:
        typer.secho("Update failed. Please run the upgrade command manually.", fg="red")


@cli.command()
def setup() -> None:
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
    cli()
