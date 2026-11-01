import json
import os
import platform
import urllib.request
from pathlib import Path

from muplayer.infrastructure.system.paths import get_bin_dir, get_libs_dir

_LIBMPV_ASSETS: dict[str, str] = {
    "Linux": "libmpv.so.2",
    "Darwin": "libmpv.dylib",
    "Windows": "libmpv-2.dll",
}


def get_detected_os() -> str:
    """Returns the current operating system name (e.g. 'Linux', 'Darwin', 'Windows')."""
    return platform.system()


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


def install_defaults() -> list[tuple[str, bool, str]]:
    """Downloads the default assets (qjs + libmpv) for the current OS from the MuPlayer GitHub release.

    Returns a list of (asset_name, success, message) for each attempted download.
    """
    system = get_detected_os()
    arch = platform.machine().lower()
    arch_tag = "x86_64" if arch in ("x86_64", "amd64") else ("arm64" if arch in ("arm64", "aarch64") else arch)
    os_tag = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}.get(system, system.lower())

    results = []

    # QuickJS runtime
    qjs_name = "qjs.exe" if system == "Windows" else "qjs"
    ok, msg = download_github_asset(f"qjs-{os_tag}-{arch_tag}", get_bin_dir(), target_filename=qjs_name)
    results.append(("quickjs", ok, msg))

    # libmpv shared library (all platforms)
    libmpv_filename = _LIBMPV_ASSETS.get(system)
    if libmpv_filename:
        ok, msg = download_github_asset(libmpv_filename, get_libs_dir(), target_filename=libmpv_filename)
        results.append(("libmpv", ok, msg))

    return results
