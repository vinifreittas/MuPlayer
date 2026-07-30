"""
Centralized path management for MuPlayer using platformdirs.

This module ensures all application data is stored in OS-standard directories,
making the application completely independent of the Current Working Directory (CWD).

Directories resolved:
- Linux:   ~/.local/share/MuPlayer/, ~/.cache/MuPlayer/, ~/.local/state/MuPlayer/logs/
- macOS:   ~/Library/Application Support/MuPlayer/
- Windows: C:\\Users\\<user>\\AppData\\Local\\vinifreittas\\MuPlayer\\
"""

from pathlib import Path

from platformdirs import user_cache_dir, user_data_dir, user_log_dir

APP_NAME = "MuPlayer"
APP_AUTHOR = "vinifreittas"


def get_data_dir() -> Path:
    """Returns the platform-appropriate directory for persistent app data (DB, config)."""
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_log_dir() -> Path:
    """Returns the platform-appropriate directory for application log files."""
    path = Path(user_log_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_dir() -> Path:
    """Returns the platform-appropriate directory for disk cache storage."""
    path = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path
