import logging
import os
from contextlib import suppress
from datetime import datetime
from pathlib import Path

from textual.logging import TextualHandler

LOG_BACKUPS = int(os.getenv("APP_LOG_BACKUPS", "5"))

# External libraries that produce noisy INFO/DEBUG output irrelevant to MuPlayer diagnostics.
_NOISY_EXTERNAL_LOGGERS = ["yt_dlp", "tortoise", "asyncio", "httpx", "urllib3", "charset_normalizer"]


def setup_logging(log_dir: Path, log_level: int = logging.INFO) -> logging.Logger:
    """Configures daily date-based log files and caps the total log count."""
    log_dir.mkdir(parents=True, exist_ok=True)

    # 1. Housekeeping: Clean up oldest logs using slicing and suppress
    existing_logs = sorted(log_dir.glob("app-*.log"), key=lambda f: f.stat().st_mtime)
    excess_count = len(existing_logs) - LOG_BACKUPS + 1

    if excess_count > 0:
        for old_log in existing_logs[:excess_count]:
            with suppress(OSError):
                old_log.unlink()

    # 2. Generate current date filename (resolved to absolute path)
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = (log_dir / f"app-{date_str}.log").resolve()

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 3. Silence noisy external loggers — keep WARNING and above only
    for lib in _NOISY_EXTERNAL_LOGGERS:
        logging.getLogger(lib).setLevel(logging.WARNING)

    # 4. Textual UI Handler Idempotency
    if not any(isinstance(h, TextualHandler) for h in root_logger.handlers):
        root_logger.addHandler(TextualHandler())

    # 5. Smart File Handler Management
    file_handler_exists = False
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.FileHandler):
            if handler.baseFilename == str(log_file):
                file_handler_exists = True
            else:
                root_logger.removeHandler(handler)
                handler.close()

    if not file_handler_exists:
        log_format = logging.Formatter(
            "[%(asctime)s] %(levelname)-8s [%(name)s:%(lineno)d] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)

    root_logger.debug("Logging initialized. File: %s | Level: %s", log_file, logging.getLevelName(log_level))
    return root_logger
