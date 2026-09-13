import json
import os
import platform
import shutil
import subprocess
import urllib.request
from pathlib import Path

from muplayer.infrastructure.system.paths import get_bin_dir, get_libs_dir


def get_detected_os() -> str:
    """Returns the current operating system name (e.g. 'Linux', 'Darwin', 'Windows')."""
    return platform.system()


def get_package_manager() -> str | None:
    """Detects available system package manager."""
    system = get_detected_os()
    if system == "Windows" and shutil.which("winget"):
        return "winget"
    if system == "Darwin" and shutil.which("brew"):
        return "brew"
    if system == "Linux":
        if shutil.which("apt-get"):
            return "apt-get"
        if shutil.which("pacman"):
            return "pacman"
        if shutil.which("dnf"):
            return "dnf"
    return None


def download_github_asset(asset_keyword: str, dest_dir: Path, target_filename: str | None = None) -> tuple[bool, str]:
    """Downloads a precompiled binary asset from the latest GitHub release of vinifreittas/MuPlayer.

    Files are stored in user-local directories without requiring elevated root/admin privileges.
    """
    api_url = "https://api.github.com/repos/vinifreittas/MuPlayer/releases/latest"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "MuPlayer-Installer"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        assets = data.get("assets", [])
        matched_url = None
        asset_name = None

        for asset in assets:
            name = asset.get("name", "").lower()
            if asset_keyword.lower() in name:
                matched_url = asset.get("browser_download_url")
                asset_name = asset.get("name")
                break

        if not matched_url or not asset_name:
            return False, f"Asset matching keyword '{asset_keyword}' was not found in latest GitHub release."

        out_name = target_filename or asset_name
        dest_file = dest_dir / out_name

        from rich.progress import BarColumn, DownloadColumn, Progress, SpinnerColumn, TextColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task(f"Downloading {out_name}...", total=None)

            dl_req = urllib.request.Request(matched_url, headers={"User-Agent": "MuPlayer-Installer"})
            with urllib.request.urlopen(dl_req, timeout=30) as response:
                total_size = int(response.headers.get("content-length", 0))
                if total_size:
                    progress.update(task, total=total_size)

                with open(dest_file, "wb") as f:
                    while chunk := response.read(8192):
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))

        if get_detected_os() != "Windows":
            os.chmod(dest_file, 0o755)

        return True, f"✓ Successfully installed {dest_file.name} to {dest_dir}!"
    except Exception as e:
        return False, f"Failed to download asset from GitHub: {e}"


def install_engine(engine_name: str) -> tuple[bool, str]:
    """Executes installation for the chosen engine via system package manager or direct GitHub download.

    Supported engines: 'mpv', 'vlc', 'quickjs', 'qjs', 'node', 'nodejs'.
    Returns (success: bool, detail_message: str).
    """
    engine = engine_name.lower().strip()
    if engine not in ("mpv", "vlc", "quickjs", "qjs", "node", "nodejs"):
        return False, f"Invalid engine choice '{engine_name}'. Must be 'mpv', 'vlc', 'quickjs', or 'node'."

    system = get_detected_os()

    # Try native system package manager first
    success, msg = False, ""
    match system:
        case "Windows":
            success, msg = _install_windows(engine)
        case "Darwin":
            success, msg = _install_macos(engine)
        case "Linux":
            success, msg = _install_linux(engine)

    if success:
        return True, msg

    # Fallback to direct user-space GitHub release asset download
    arch = platform.machine().lower()
    if arch in ("x86_64", "amd64"):
        arch_tag = "x86_64"
    elif arch in ("arm64", "aarch64"):
        arch_tag = "arm64"
    else:
        arch_tag = arch

    os_tag = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}.get(system, system.lower())

    if engine in ("quickjs", "qjs"):
        keyword = f"qjs-{os_tag}-{arch_tag}"
        target_name = "qjs.exe" if system == "Windows" else "qjs"
        return download_github_asset(keyword, get_bin_dir(), target_filename=target_name)

    if engine == "mpv" and system == "Windows":
        # libmpv-2.dll is the only Windows audio lib asset bundled in the MuPlayer release
        return download_github_asset("libmpv-2.dll", get_libs_dir(), target_filename="libmpv-2.dll")

    if engine == "vlc" and system == "Windows":
        return False, "VLC on Windows requires a full installer. Please install via: winget install VideoLAN.VLC"

    return False, f"Failed to install '{engine}': {msg}"


def _install_windows(engine: str) -> tuple[bool, str]:
    if not shutil.which("winget"):
        return False, "Windows Package Manager ('winget') was not found on system PATH."

    package_ids = {
        "mpv": "xtse.mpv",
        "vlc": "VideoLAN.VLC",
        "node": "OpenJS.NodeJS",
        "nodejs": "OpenJS.NodeJS",
        "quickjs": "quickjs",
        "qjs": "quickjs",
    }
    package_id = package_ids.get(engine, engine)

    try:
        res = subprocess.run(["winget", "install", package_id], check=False)
        if res.returncode == 0:
            return True, f"✓ {engine.upper()} installed successfully via winget!"
        return False, f"winget process exited with error code {res.returncode}."
    except Exception as e:
        return False, f"Failed to execute winget: {e}"


def _install_macos(engine: str) -> tuple[bool, str]:
    if not shutil.which("brew"):
        return False, "Homebrew ('brew') was not detected on system PATH."

    if engine == "vlc":
        cmd = ["brew", "install", "--cask", "vlc"]
    elif engine in ("node", "nodejs"):
        cmd = ["brew", "install", "node"]
    else:
        cmd = ["brew", "install", engine]

    try:
        res = subprocess.run(cmd, check=False)
        if res.returncode == 0:
            return True, f"✓ {engine.upper()} installed successfully via Homebrew!"
        return False, f"Homebrew process exited with error code {res.returncode}."
    except Exception as e:
        return False, f"Failed to execute Homebrew: {e}"


def _install_linux(engine: str) -> tuple[bool, str]:
    pkg_map = {
        "mpv": {"apt-get": "libmpv-dev", "dnf": "mpv-libs", "pacman": "mpv"},
        "vlc": {"apt-get": "libvlc-dev", "dnf": "vlc-core", "pacman": "vlc"},
        "node": {"apt-get": "nodejs", "dnf": "nodejs", "pacman": "nodejs"},
        "nodejs": {"apt-get": "nodejs", "dnf": "nodejs", "pacman": "nodejs"},
        "quickjs": {"apt-get": "quickjs", "dnf": "quickjs", "pacman": "quickjs"},
        "qjs": {"apt-get": "quickjs", "dnf": "quickjs", "pacman": "quickjs"},
    }

    commands: list[list[str]] = []
    if shutil.which("apt-get"):
        pkg = pkg_map.get(engine, {}).get("apt-get", engine)
        commands = [["sudo", "apt-get", "update"], ["sudo", "apt-get", "install", "-y", pkg]]
    elif shutil.which("pacman"):
        pkg = pkg_map.get(engine, {}).get("pacman", engine)
        commands = [["sudo", "pacman", "-S", "--noconfirm", pkg]]
    elif shutil.which("dnf"):
        pkg = pkg_map.get(engine, {}).get("dnf", engine)
        commands = [["sudo", "dnf", "install", "-y", pkg]]

    if not commands:
        return False, "Could not identify a supported package manager (apt-get, pacman, dnf)."

    try:
        for cmd in commands:
            res = subprocess.run(cmd, check=False)
            if res.returncode != 0:
                return False, f"Command failed: {' '.join(cmd)}"
        return True, f"✓ {engine.upper()} installed successfully!"
    except Exception as e:
        return False, f"Package manager execution failed: {e}"
