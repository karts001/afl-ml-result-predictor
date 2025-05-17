from typing import Dict
import atexit
from contextlib import asynccontextmanager
import asyncio

from asyncpg import pool

from config import load_config    
from logger import logger

class AsyncDatabaseConnection():
    def __init__(self, config: Dict[str, str], min_conn=1, max_conn=10):
        self.config = config
        self._min_conn = min_conn
        self._max_conn = max_conn
        self.pool = None

        atexit.register(self._sync_close_all)

    async def create_connection_pool(self):
        self.pool = await pool.create_pool(
            min_size=self._min_conn,
            max_size=self._max_conn,
            **self.config
        )
        logger.info("Connection pool created")        

    @asynccontextmanager
    async def connection_from_pool(self):
        if not self.pool:
            logger.error("Connection pool not initialised")
            logger.info("Create the connection pool")
            await self.create_connection_pool()
        async with self.pool.acquire() as conn:
            yield conn
    
    async def close_all(self):
        if self.pool:
            await self.pool.close()
            logger.info("📤 All async database connections closed")
        
    def _sync_close_all(self):
        """A synchronous wrapper for graceful shutdown when the app exits."""
        # asyncio.run() cannot be called from a running event loop
        try:
            loop = asyncio.get_running_loop()
            # Use a background task or warn
            logger.warn("Cannot close pool from running event loop. Please call close_all() explicitly.")
        except RuntimeError:
            asyncio.run(self.close_all())


if __name__ == "__main__":
    db = AsyncDatabaseConnection(config=load_config())
    async_db = AsyncDatabaseConnection(config=load_config())
