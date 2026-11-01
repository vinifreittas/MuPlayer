import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from importlib.metadata import PackageNotFoundError, distribution

from muplayer import __github_repo__

_USER_AGENT = "MuPlayerUpdateChecker/1.0"
_GITHUB_COMMIT_URL = f"https://api.github.com/repos/{__github_repo__}/commits/main"


def is_running_in_venv() -> bool:
    """Returns True if the current Python process is running inside a virtual environment."""
    return sys.prefix != sys.base_prefix


def get_installed_commit_sha(package_name: str = "muplayer") -> str | None:
    """Retrieves the installed commit SHA from PEP 610 metadata."""
    try:
        dist = distribution(package_name)
        direct_url_content = dist.read_text("direct_url.json")
        if not direct_url_content:
            return None
        data = json.loads(direct_url_content)
        return data.get("vcs_info", {}).get("commit_id")
    except (PackageNotFoundError, json.JSONDecodeError, Exception) as e:
        print(f"Debug: Failed to read commit SHA: {e}")
        return None


def check_for_updates() -> tuple[bool, str | None, str | None, str | None]:
    """Queries the GitHub Commits API and compares the installed commit SHA with main.

    Returns:
        (is_update_available, installed_sha, latest_sha, error_message)
    """
    installed_sha = get_installed_commit_sha()
    if not installed_sha:
        return (
            False,
            None,
            None,
            "Could not determine installed commit SHA (not installed via Git URL).",
        )

    try:
        req = urllib.request.Request(
            _GITHUB_COMMIT_URL,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "application/vnd.github.sha",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            latest_sha = response.read().decode("utf-8").strip()

    except urllib.error.URLError as e:
        return False, installed_sha, None, f"Network error: Could not check for updates ({e.reason})."
    except Exception as e:
        return False, installed_sha, None, f"An unexpected error occurred: {e}"

    is_update_available = installed_sha != latest_sha
    return is_update_available, installed_sha, latest_sha, None


def perform_update() -> tuple[bool, str]:
    """Upgrades the muplayer package to the latest version from GitHub using uv.

    Returns:
        (success, detail_message)
    """
    uv_executable = shutil.which("uv")
    if not uv_executable:
        return False, "Error: 'uv' executable not found in PATH."

    git_url = f"git+https://github.com/{__github_repo__}.git"
    command = [uv_executable, "tool", "install", git_url, "--reinstall"]

    try:
        subprocess.run(command, check=True)
        return True, "✓ MuPlayer updated successfully via uv!"
    except subprocess.CalledProcessError as e:
        return False, f"Update failed using uv. Please run 'uv tool install {git_url} --reinstall' manually. ({e})"
