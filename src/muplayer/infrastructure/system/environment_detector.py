import importlib.metadata
import shutil
import subprocess
import sys
from ctypes.util import find_library


def get_version() -> str:
    """Dynamically fetches the installed package version."""
    try:
        return importlib.metadata.version("muplayer")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.1 (local/dev)"


def check_engines() -> dict[str, str | None]:
    """Checks if mpv or vlc shared libraries are present on the system."""
    return {"mpv": find_library("mpv"), "vlc": find_library("vlc")}


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
        return output.splitlines()[0] if output else "Installed"
    except Exception:
        return "Installed"


def check_terminal_support() -> tuple[bool, str | None]:
    """Checks if the terminal environment supports running the Textual TUI."""
    from rich.console import Console

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


def get_terminal_dimensions() -> tuple[int, int]:
    """Returns current terminal dimensions as (columns, lines)."""
    cols, lines = shutil.get_terminal_size()
    return cols, lines
