import json
import logging
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AppConfig(BaseModel):
    language: str = "en"
    efficiency_mode: bool = False
    search_limit: int = 15
    volume: int = 80


class ConfigManager:
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
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()
