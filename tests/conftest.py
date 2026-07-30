"""
Pytest configuration and shared fixtures for the MuPlayer test suite.

Fixtures:
- db_manager: provides an in-memory DatabaseManager (SQLite :memory:) for fast, isolated tests.
"""

from pathlib import Path

import pytest_asyncio

from muplayer.database.manager import DatabaseManager


@pytest_asyncio.fixture
async def db_manager(tmp_path: Path) -> DatabaseManager:
    """
    Provides an isolated DatabaseManager backed by a temporary SQLite file.
    Automatically connects before the test and disconnects after.
    """
    db_path = tmp_path / "test_app_data.db"
    manager = DatabaseManager(db_path=db_path)
    await manager.connect()
    yield manager
    await manager.disconnect()
