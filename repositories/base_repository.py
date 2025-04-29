from typing import Any, List, Tuple
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as Connection


class BaseRepository():
    def __init__(self, conn: Connection):
        self.conn = conn

    def fetch_one(self, query: str, params: Tuple[Any, ...] = ()):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        except Exception as e:
            print(f"❌ Failed to add rows. {e}")
        
    def execute_batch(self, query: str, params: List[Tuple[Any, ...]]):
        try:
            with self.conn.cursor() as cursor:
                psycopg2.extras.execute_batch(cursor, query, params)
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Failed to add rows. {e}")
    
    def get_columns_placeholders_and_values(self, dtos: List[Any]):
        fields = dtos[0].model_dump(by_alias=True).keys()
        placeholders = ", ".join([r"%s"] * len(fields))
        columns = ", ".join(fields)
        values = [tuple(dto.model_dump().values()) for dto in dtos]


        return columns, placeholders, values