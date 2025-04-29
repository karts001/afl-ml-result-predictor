from typing import Dict
import atexit

import psycopg2
from psycopg2.extensions import connection as Connection

from config import load_config

class Database:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.conn = self.connect()
        atexit.register(self.conn.close)

    def connect(self) -> Connection:
        try:
            with psycopg2.connect(**self.config) as conn:
                print("✅ Connected to the neon db postgres server")
                return conn
        except (psycopg2.DatabaseError, Exception) as error:
            print("❌ Connection failed:", error)
                    

if __name__ == "__main__":
    db = Database(config=load_config())
