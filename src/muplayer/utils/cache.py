import logging
from pathlib import Path
from types import TracebackType
from typing import Any

import diskcache

logger = logging.getLogger(__name__)


class Cache:
    def __init__(self, cache_dir: Path):
        self.cache = diskcache.Cache(cache_dir)
        logger.info(f"Disk cache initialized at: {cache_dir}")

    def set(self, key: str, value: Any, expire: int | None = None) -> bool:
        """Set a value in the cache."""
        try:
            return self.cache.set(key, value, expire=expire)
        except Exception as e:
            logger.error(f"Failed to set cache key '{key}': {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the cache. Returns default if key does not exist."""
        return self.cache.get(key, default=default)

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        return key in self.cache

    def delete(self, key: str) -> bool:
        """Delete a key from the cache. Returns True if the key existed."""
        return self.cache.delete(key)

    def clear(self) -> int:
        """Clear all items from the cache. Returns the number of items removed."""
        return self.cache.clear()

    def close(self) -> None:
        """Close the underlying SQLite database connection safely."""
        self.cache.close()
        logger.debug("Cache closed successfully.")

    def __contains__(self, key: str) -> bool:
        """Allows syntax like: if 'key' in cache:"""
        return self.exists(key)

    def __enter__(self) -> "Cache":
        """Support usage as a context manager: with Cache(...) as cache:"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Ensures the cache is closed even if an exception occurs."""
        self.close()
