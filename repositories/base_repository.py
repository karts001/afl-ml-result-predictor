from typing import Any, List, Optional, Tuple
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as Connection

from database import DatabaseConnectionManager

class BaseRepository():
    def __init__(self, db_manager: Optional[DatabaseConnectionManager]):
        self.db_manager = db_manager

    def fetch_one(self, query: str, params: Tuple[Any, ...] = ()):
        try:            
            with self.db_manager.connection_from_pool() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone()
        except (Exception, psycopg2.DatabaseError) as e:
            print(f"❌ Failed to retrieve row. {e}")
            raise

        
    def execute_batch(self, query: str, params: List[Tuple[Any, ...]]):
        try:
            with self.db_manager.connection_from_pool() as conn:
                with conn.cursor() as cursor:
                    psycopg2.extras.execute_batch(cursor, query, params)
                conn.commit()
        except (Exception, psycopg2.DatabaseError) as e:
            conn.rollback()
            print(f"❌ Failed to add rows. {e}")
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
    