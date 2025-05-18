from typing import Any, List, Optional, Tuple
from logger import logger

import asyncpg

from database import AsyncDatabaseConnection

class BaseRepository():
    def __init__(self, db_manager: Optional[AsyncDatabaseConnection]):
        self.db_manager = db_manager

    async def fetch_one(self, query: str, params: Tuple[Any, ...] = ()):
        try:            
            async with self.db_manager.connection_from_pool() as conn:
                result = await conn.fetchrow(query, *params)
                return result
        except (Exception, asyncpg.InterfaceError) as e:
            logger.error(f"Failed to retrieve row: {e}")
            raise

        
    async def execute_batch(self, query: str, params: List[Tuple[Any, ...]]):
        try:
            async with self.db_manager.connection_from_pool() as conn:
                result = await conn.executemany(query, params)
                return result
        except (Exception, asyncpg.InterfaceError) as e:
            logger.error(f"Failed to execute batch: {e}")
            raise
    
    def get_columns_placeholders_and_values(self, dtos: set[Any]):
        if not dtos:
            raise ValueError("DTO set is empty")
        sample_dto = next(iter(dtos)) # can't index sets so use this instead
        fields = sample_dto.model_dump(by_alias=True).keys()
        placeholders = ", ".join([r"%s"] * len(fields))
        columns = ", ".join(fields)
        values = [tuple(dto.model_dump().values()) for dto in dtos]

        return columns, placeholders, values
    