import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

from packaging.version import parse as parse_version

from muplayer import __github_repo__

_USER_AGENT = "MuPlayerUpdateChecker/1.0"
_GITHUB_RELEASES_URL = f"https://api.github.com/repos/{__github_repo__}/releases/latest"


def is_running_in_venv() -> bool:
    """Returns True if the current Python process is running inside a virtual environment."""
    return sys.prefix != sys.base_prefix


def check_for_updates(current_ver: str) -> tuple[bool, str, str | None]:
    """Queries the GitHub Releases API and compares with the installed version.

    Returns:
        (is_update_available, latest_tag, error_message)
        - is_update_available: True if a newer version is available.
        - latest_tag: The latest version tag string (e.g. "1.2.3").
        - error_message: A human-readable error string, or None on success.
    """
    try:
        req = urllib.request.Request(
            _GITHUB_RELEASES_URL,
            headers={"User-Agent": _USER_AGENT},
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            latest_tag = data["tag_name"].lstrip("v")

    except urllib.error.URLError as e:
        return False, "", f"Network error: Could not check for updates ({e.reason})."
    except json.JSONDecodeError:
        return False, "", "Error: Failed to parse update response from GitHub."
    except Exception as e:
        return False, "", f"An unexpected error occurred: {e}"

    is_newer = parse_version(latest_tag) > parse_version(current_ver)
    return is_newer, latest_tag, None


def perform_update() -> tuple[bool, str]:
    """Upgrades the muplayer package to the latest version from GitHub using uv or pip.

    Returns:
        (success, detail_message)
        - success: True if the upgrade command exited successfully.
        - detail_message: Human-readable success or failure message.
    """
    git_url = f"git+https://github.com/{__github_repo__}.git"

    if shutil.which("uv"):
        command = ["uv", "pip", "install", "--upgrade", "--python", sys.executable, git_url]
        tool = "uv"
    else:
        command = [sys.executable, "-m", "pip", "install", "--upgrade", git_url]
        tool = "pip"

    try:
        subprocess.run(command, check=True)
        return True, f"✓ MuPlayer updated successfully via {tool}!"
    except subprocess.CalledProcessError:
        return False, f"Update failed using {tool}. Please run the upgrade command manually."
