"""
Database connection management with connection pooling.
"""
import aiosqlite
import logging
from typing import Optional
from contextlib import asynccontextmanager
from src.config.config import DATABASE_FILE as DB_NAME

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections with connection pooling."""
    
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def get_connection(self) -> aiosqlite.Connection:
        """Get a database connection, creating one if needed."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            # Enable WAL mode for better concurrency
            await self._connection.execute("PRAGMA journal_mode=WAL")
            # Enable foreign keys
            await self._connection.execute("PRAGMA foreign_keys=ON")
            # Optimize for performance
            await self._connection.execute("PRAGMA synchronous=NORMAL")
            await self._connection.execute("PRAGMA cache_size=10000")
            await self._connection.execute("PRAGMA temp_store=MEMORY")
            logger.info("Database connection established")
        return self._connection
    
    async def close(self):
        """Close the database connection."""
        if self._connection:
            try:
                await self._connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing database connection: {e}")
            finally:
                self._connection = None
    
    @asynccontextmanager
    async def get_cursor(self):
        """Get a database cursor with automatic cleanup."""
        conn = await self.get_connection()
        cursor = await conn.cursor()
        try:
            yield cursor
        finally:
            await cursor.close()

# Global database manager instance
db_manager = DatabaseManager()

@asynccontextmanager
async def get_db_connection():
    """Context manager for database connections."""
    conn = await db_manager.get_connection()
    try:
        yield conn
    finally:
        # Don't close here, let the manager handle it
        pass

@asynccontextmanager
async def get_db_cursor():
    """Context manager for database cursors."""
    async with db_manager.get_cursor() as cursor:
        yield cursor
