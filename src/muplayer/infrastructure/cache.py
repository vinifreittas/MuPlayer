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
            result = self.cache.set(key, value, expire=expire)
            logger.debug(f"Cache set for key '{key}'. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to set cache key '{key}': {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the cache. Returns default if key does not exist."""
        try:
            result = self.cache.get(key, default=default)
            logger.debug(f"Cache get for key '{key}'. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to get cache key '{key}': {e}")
            return default

    def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        try:
            result = key in self.cache
            logger.debug(f"Cache exists for key '{key}'. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to check cache key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a key from the cache. Returns True if the key existed."""
        try:
            result = self.cache.delete(key)
            logger.debug(f"Cache delete for key '{key}'. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete cache key '{key}': {e}")
            return False

    def clear(self) -> int:
        """Clear all items from the cache. Returns the number of items removed."""
        try:
            result = self.cache.clear()
            logger.debug(f"Cache cleared. Result: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return 0

    def close(self) -> None:
        """Close the underlying SQLite database connection safely."""
        try:
            self.cache.close()
            logger.debug("Cache closed successfully.")
        except Exception as e:
            logger.error(f"Failed to close cache: {e}")

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
