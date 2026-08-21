from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from muplayer.infrastructure.config import AppConfig


class ConfigPort(ABC):
    """Port defining the contract for application configuration management."""

    @abstractmethod
    def load(self) -> AppConfig:
        """Load configuration from the persistent source."""
        ...

    @abstractmethod
    def save(self) -> None:
        """Persist current configuration."""
        ...

    @abstractmethod
    def get(self) -> AppConfig:
        """Return the current in-memory configuration."""
        ...

    @abstractmethod
    def update(self, **kwargs: Any) -> None:
        """Update configuration fields and persist."""
        ...
