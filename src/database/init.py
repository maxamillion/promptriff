"""Database initialization script."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import settings
from src.database.models import Database


async def init_database():
    """Initialize the database."""
    config = settings.load()
    db_path = config.database.path
    
    print(f"Initializing database at: {db_path}")
    
    db = Database(db_path)
    await db.initialize()
    
    print("Database initialized successfully!")
    
    # Create backup if configured
    if config.database.backup_on_startup:
        backup_path = await db.backup()
        print(f"Database backed up to: {backup_path}")


def main():
    """Main entry point."""
    asyncio.run(init_database())


if __name__ == "__main__":
    main()