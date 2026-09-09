from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from muplayer.infrastructure.i18n import set_locale

if TYPE_CHECKING:
    from muplayer.application.ports.config_port import ConfigPort
    from muplayer.domain.config import AppConfig

logger = logging.getLogger(__name__)


class ConfigService:
    """Application service for orchestrating user preferences and configuration side-effects."""

    def __init__(self, config_port: ConfigPort) -> None:
        self._config_port = config_port

    @property
    def config(self) -> AppConfig:
        """Return current application configuration."""
        return self._config_port.get()

    def update(self, **kwargs: Any) -> AppConfig:
        """Update configuration properties and trigger system side-effects."""
        self._config_port.update(**kwargs)

        if "language" in kwargs:
            set_locale(kwargs["language"])

        return self.config

    def update_volume(self, volume: int) -> int:
        """Update volume setting (clamped between 0 and 100)."""
        clamped_vol = max(0, min(volume, 100))
        self.update(volume=clamped_vol)
        return clamped_vol
