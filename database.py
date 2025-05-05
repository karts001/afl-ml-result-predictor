from typing import Dict
import atexit
from contextlib import contextmanager

from psycopg2 import pool
from psycopg2.extensions import connection as Connection

from config import load_config

class DatabaseConnectionManager:
    def __init__(self, config: Dict[str, str], min_conn=1, max_conn=10):
        self.pool = pool.SimpleConnectionPool(
            min_conn,
            max_conn,
            **config
        )

        atexit.register(self.close_all) # register this function for when the script exits

    @contextmanager
    def connection_from_pool(self):
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            if conn and not conn.closed:
                self.pool.putconn(conn)

    def close_all(self):
        print("📤 All database connections closed")
        if self.pool:
            self.pool.closeall()                    

if __name__ == "__main__":
    db = DatabaseConnectionManager(config=load_config())
