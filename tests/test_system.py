from unittest.mock import patch

from muplayer.infrastructure.system import (
    check_engines,
    detect_js_runtime,
    get_bin_dir,
    get_libs_dir,
    install_engine,
)


def test_paths_resolution():
    """Validates that the new binary and library directories are valid Paths."""
    bin_dir = get_bin_dir()
    libs_dir = get_libs_dir()

    assert bin_dir.name == "bin"
    assert libs_dir.name == "libs"
    assert bin_dir.exists()
    assert libs_dir.exists()


def test_environment_detector_local_libs(tmp_path):
    """Validates that check_engines detects libraries in the user's local directory."""
    with (
        patch("muplayer.infrastructure.system.environment_detector.get_libs_dir", return_value=tmp_path),
        patch("muplayer.infrastructure.system.environment_detector.find_library", return_value=None),
    ):
        # Create dummy lib file
        fake_lib = tmp_path / "libmpv.so.2"
        fake_lib.touch()

        engines = check_engines()
        assert engines["mpv"] == str(fake_lib)


def test_environment_detector_local_binaries(tmp_path):
    """Validates that detect_js_runtime detects qjs in the local binary directory."""
    with (
        patch("muplayer.infrastructure.system.environment_detector.get_bin_dir", return_value=tmp_path),
        patch("shutil.which", return_value=None),
    ):
        fake_qjs = tmp_path / "qjs"
        fake_qjs.touch()

        runtime = detect_js_runtime()
        assert runtime is not None
        assert "quickjs" in runtime
        assert runtime["quickjs"]["path"] == str(fake_qjs)


def test_engine_installer_invalid_engine():
    """Validates that an invalid engine choice is rejected with a friendly error."""
    success, msg = install_engine("invalid_engine")
    assert success is False
    assert "Invalid engine choice" in msg


def test_engine_installer_github_download_fallback():
    """Validates the GitHub API download fallback when the package manager fails."""
    with (
        patch("muplayer.infrastructure.system.engine_installer._install_linux", return_value=(False, "Failed")),
        patch("muplayer.infrastructure.system.engine_installer.download_github_asset") as mock_dl,
    ):
        mock_dl.return_value = (True, "Installed from GitHub")
        success, msg = install_engine("quickjs")
        assert success is True
        assert "Installed from GitHub" in msg
        mock_dl.assert_called_once()
