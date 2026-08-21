import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

from muplayer.application.ports import ConfigPort

logger = logging.getLogger(__name__)


class AppConfig(BaseModel):
    language: str = Field(default="en", pattern="^(en|pt)$")
    efficiency_mode: bool = False
    search_limit: int = Field(default=15, ge=1, le=50)
    volume: int = Field(default=80, ge=0, le=100)


class ConfigManager(ConfigPort):
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self.load()

    def load(self) -> AppConfig:
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    data = json.load(f)
                    return AppConfig.model_validate(data)
            except Exception as e:
                logger.error(f"Failed to load config: {e}")

        # Return default if not exists or failed to parse
        return AppConfig()

    def save(self) -> None:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config.model_dump(), f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

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
            logger.error(f"Failed to update config with kwargs {kwargs}: {e}")
