import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

import typer

from muplayer import __github_repo__
from muplayer.cli.utils import get_version

USER_AGENT = "MuPlayerUpdateChecker/1.0"
GITHUB_REPO = __github_repo__

app = typer.Typer()


@app.command("update")
def update_cmd() -> None:
    """Update the program to the latest version."""
    from packaging.version import parse as parse_version

    from muplayer.utils import t

    typer.echo("Checking for the latest version on GitHub...")
    current_ver = get_version()

    if "dev" in current_ver:
        typer.secho("You are running a local development version. Update skipped.", fg="yellow")
        return

    if sys.prefix == sys.base_prefix:
        typer.secho(t("update_outside_venv"), fg="yellow")
        if not typer.confirm("Continue anyway?", default=False):
            raise typer.Exit()

    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            latest_tag = data["tag_name"].lstrip("v")

    except urllib.error.URLError as e:
        typer.secho(f"Network error: Could not check for updates ({e.reason}).", fg="red")
        raise typer.Exit(code=1) from None

    except json.JSONDecodeError:
        typer.secho("Error: Failed to parse update response from GitHub.", fg="red")
        raise typer.Exit(code=1) from None

    except Exception as e:
        typer.secho(f"An unexpected error occurred: {e}", fg="red")
        raise typer.Exit(code=1) from None

    latest_version = parse_version(latest_tag)
    current_version = parse_version(current_ver)

    if latest_version <= current_version:
        typer.secho(f"You are already up to date! (v{current_ver})", fg="green")
        return

    typer.echo(f"A new version is available: v{latest_tag} (Current: v{current_ver})")
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
