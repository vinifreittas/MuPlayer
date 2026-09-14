from unittest.mock import MagicMock

from muplayer.interface.tui.controllers.base import safe_call_from_thread


def test_safe_call_from_thread_when_running():
    target = MagicMock()
    target.is_running = True
    func = MagicMock()

    safe_call_from_thread(target, func, "arg1", kw="kw1")

    target.call_from_thread.assert_called_once_with(func, "arg1", kw="kw1")


def test_safe_call_from_thread_when_not_running():
    target = MagicMock()
    target.is_running = False
    func = MagicMock()

    safe_call_from_thread(target, func, "arg1")

    target.call_from_thread.assert_not_called()


def test_safe_call_from_thread_suppresses_runtime_error():
    target = MagicMock()
    target.is_running = True
    target.call_from_thread.side_effect = RuntimeError("App is not running")
    func = MagicMock()

    # Should not raise exception
    safe_call_from_thread(target, func, "arg1")
    target.call_from_thread.assert_called_once_with(func, "arg1")
