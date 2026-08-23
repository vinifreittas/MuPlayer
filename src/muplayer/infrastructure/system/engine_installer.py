import platform
import shutil
import subprocess


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


def install_engine(engine_name: str) -> tuple[bool, str]:
    """Executes native OS package manager installation for the chosen engine.

    Supported engines: 'mpv', 'vlc', 'quickjs', 'node', 'nodejs'.
    Returns (success: bool, detail_message: str).
    """
    engine = engine_name.lower().strip()
    if engine not in ("mpv", "vlc", "quickjs", "node", "nodejs"):
        return False, f"Invalid engine choice '{engine_name}'. Must be 'mpv', 'vlc', 'quickjs', or 'node'."

    system = get_detected_os()

    match system:
        case "Windows":
            return _install_windows(engine)
        case "Darwin":
            return _install_macos(engine)
        case "Linux":
            return _install_linux(engine)
        case _:
            return False, f"Unsupported operating system: {system}."


def _install_windows(engine: str) -> tuple[bool, str]:
    if not shutil.which("winget"):
        return False, "Windows Package Manager ('winget') was not found on system PATH."

    package_ids = {
        "mpv": "xtse.mpv",
        "vlc": "VideoLAN.VLC",
        "node": "OpenJS.NodeJS",
        "nodejs": "OpenJS.NodeJS",
        "quickjs": "quickjs",
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
    pkg_name = "nodejs" if engine in ("node", "nodejs") else engine
    commands: list[list[str]] = []

    if shutil.which("apt-get"):
        commands = [["sudo", "apt-get", "update"], ["sudo", "apt-get", "install", "-y", pkg_name]]
    elif shutil.which("pacman"):
        commands = [["sudo", "pacman", "-S", "--noconfirm", pkg_name]]
    elif shutil.which("dnf"):
        commands = [["sudo", "dnf", "install", "-y", pkg_name]]

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
