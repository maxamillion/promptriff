"""Pytest configuration and fixtures."""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from promptriff.config import Settings
from promptriff.database import DatabaseManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_dir: Path) -> Settings:
    """Create test settings."""
    return Settings(
        models={
            "openai": {
                "api_key": "test-openai-key",
                "endpoint": "https://test.openai.com/v1",
                "default_model": "gpt-3.5-turbo"
            },
            "claude": {
                "api_key": "test-claude-key",
                "endpoint": "https://test.anthropic.com/v1",
                "default_model": "claude-3-haiku-20240307"
            }
        },
        mcp_tools=[],
        ui={
            "theme": "dark",
            "editor": "vim",
            "diff_syntax_highlighting": True,
            "max_response_lines": 1000,
            "autosave_interval": 60
        },
        database={
            "path": str(temp_dir / "test.db"),
            "backup_on_startup": False,
            "vacuum_on_startup": False
        },
        debug=True
    )


@pytest_asyncio.fixture
async def db_manager(test_settings: Settings) -> AsyncGenerator[DatabaseManager, None]:
    """Create a test database manager."""
    manager = DatabaseManager(f"sqlite:///{test_settings.database.path}")
    await manager.create_tables()
    yield manager
    await manager.close()


@pytest_asyncio.fixture
async def db_session(db_manager: DatabaseManager) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with db_manager.async_session() as session:
        yield session