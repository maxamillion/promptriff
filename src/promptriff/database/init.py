"""Database initialization script."""

import asyncio
import sys
from pathlib import Path

from ..config import load_settings
from .models import DatabaseManager


async def init_database():
    """Initialize the database."""
    try:
        # Load settings
        settings = load_settings()
        
        # Get database path
        db_path = Path(settings.database.path).expanduser()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create database URL
        db_url = f"sqlite:///{db_path}"
        
        # Initialize database manager
        db_manager = DatabaseManager(db_url)
        
        print(f"Initializing database at: {db_path}")
        
        # Create tables
        await db_manager.create_tables()
        
        print("Database initialized successfully!")
        
        # Close connections
        await db_manager.close()
        
    except Exception as e:
        print(f"Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(init_database())