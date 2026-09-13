import importlib.metadata
import shutil
import subprocess
import sys
from ctypes.util import find_library
from pathlib import Path

import installed_browsers

from muplayer.infrastructure.system.paths import get_bin_dir, get_libs_dir

# Supported JS runtimes by yt-dlp, in preferred detection order.
_JS_RUNTIME_CANDIDATES: list[str] = ["quickjs", "qjs", "node", "deno", "bun"]


def get_version() -> str:
    """Dynamically fetches the installed package version."""
    try:
        return importlib.metadata.version("muplayer")
    except importlib.metadata.PackageNotFoundError:
        return "0.0.1 (local/dev)"


def _check_local_lib(engine_name: str) -> str | None:
    """Checks for engine shared library files in the user's local libs directory."""
    libs_dir = get_libs_dir()
    patterns = {
        "mpv": ["*mpv*.dll", "*mpv*.so*", "*mpv*.dylib"],
        "vlc": ["*vlc*.dll", "*vlc*.so*", "*vlc*.dylib"],
    }
    for pattern in patterns.get(engine_name, []):
        matches = list(libs_dir.glob(pattern))
        if matches:
            return str(matches[0])
    return None


def check_engines() -> dict[str, str | None]:
    """Checks if mpv or vlc shared libraries are present on the system or in user libs dir."""
    return {
        "mpv": find_library("mpv") or _check_local_lib("mpv"),
        "vlc": find_library("vlc") or _check_local_lib("vlc"),
    }


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


def get_default_browser() -> str:
    """Detects the system's default browser for yt-dlp cookie extraction.

    Falls back to 'firefox' if no known browser is detected.
    """
    browser_options = [
        "brave",
        "chrome",
        "chromium",
        "edge",
        "firefox",
        "opera",
        "safari",
        "vivaldi",
        "librewolf",
        "waterfox",
        "floorp",
        "whale",
    ]
    raw_browser = installed_browsers.what_is_the_default_browser()
    if raw_browser:
        name = str(raw_browser).lower()
        for option in browser_options:
            if option in name:
                return option
    return "firefox"


def detect_js_runtime() -> dict[str, dict] | None:
    """Detects the first available JavaScript runtime on PATH or local bin directory.

    Probes candidates in order: quickjs → qjs → node → deno → bun.
    Returns a yt-dlp-compatible ``js_runtimes`` dict, e.g. ``{'quickjs': {'path': '/path/to/qjs'}}``,
    or ``None`` if none is found.
    """
    bin_dir = get_bin_dir()
    for runtime in _JS_RUNTIME_CANDIDATES:
        path = shutil.which(runtime)
        if path:
            key = "quickjs" if runtime in ("quickjs", "qjs") else runtime
            return {key: {"path": path}}

        # Check local user bin directory
        for ext in ("", ".exe"):
            local_bin = Path(bin_dir) / f"{runtime}{ext}"
            if local_bin.is_file():
                key = "quickjs" if runtime in ("quickjs", "qjs") else runtime
                return {key: {"path": str(local_bin)}}

    return None
