import logging
from pathlib import Path

from muplayer.application.ports import ConfigPort
from muplayer.domain import AppConfig

logger = logging.getLogger(__name__)


class ConfigManager(ConfigPort):
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self.load()

    def load(self) -> AppConfig:
        if self.config_path.exists():
            try:
                return AppConfig.model_validate_json(self.config_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error("Failed to load config from '%s': %s", self.config_path, e, exc_info=True)

        # Return default if not exists or failed to parse
        return AppConfig()

    def save(self) -> None:
        try:
            self.config_path.write_text(self.config.model_dump_json(indent=4), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to save config to '%s': %s", self.config_path, e, exc_info=True)

    def get(self) -> AppConfig:
        return self.config

    def update(self, **kwargs) -> None:
        """Update configuration fields safely, validating against AppConfig schema."""
        try:
            current_data = self.config.model_dump()
            current_data.update(kwargs)
            self.config = AppConfig.model_validate(current_data)
            self.save()
        except Exception as e:
            logger.error(
                "Failed to update config at '%s' with kwargs %s: %s", self.config_path, kwargs, e, exc_info=True
            )
