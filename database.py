import datetime
from typing import Any, Dict, List, Tuple
import atexit

import psycopg2
from psycopg2.extensions import connection as Connection
from psycopg2.extras import execute_values, execute_batch


from dtos.games_dto import GameDTO
from dtos.stats_dto import PlayerMatchStatsDTO
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
    
    def create_database_schema(self) -> None:
        # connect to database and add dataframes to a database while ignore the index
            schema_sql = """
                CREATE TABLE IF NOT EXISTS players (
                    PlayerId TEXT PRIMARY KEY,
                    DisplayName TEXT,
                    Height INTEGER,
                    Weight INTEGER,
                    Dob TEXT,
                    Position TEXT,
                    Origin TEXT
                );

                CREATE TABLE IF NOT EXISTS games (
                    GameId TEXT PRIMARY KEY,
                    Year INTEGER,
                    Round TEXT,
                    Date TEXT,
                    MaxTemp REAL,
                    MinTemp REAL,
                    Rainfall REAL,
                    Venue TEXT,
                    StartTime TEXT,
                    Attendance INTEGER,
                    HomeTeam TEXT,
                    HomeTeamScoreQT TEXT,
                    HomeTeamScoreHT TEXT,
                    HomeTeamScore3QT TEXT,
                    HomeTeamScoreFT TEXT,
                    HomeTeamScore INTEGER,
                    AwayTeam TEXT,
                    AwayTeamScoreQT TEXT,
                    AwayTeamScoreHT TEXT,
                    AwayTeamScore3QT TEXT,
                    AwayTeamScoreFT TEXT,
                    AwayTeamScore INTEGER
                );

                CREATE TABLE IF NOT EXISTS stats (
                    GameId TEXT,
                    Team TEXT,
                    Year INTEGER,
                    Round TEXT,
                    PlayerId TEXT,
                    DisplayName TEXT,
                    GameNumber INTEGER,
                    Disposals INTEGER,
                    Kicks INTEGER,
                    Marks INTEGER,
                    Handballs INTEGER,
                    Goals INTEGER,
                    Behinds INTEGER,
                    HitOuts INTEGER,
                    Tackles INTEGER,
                    Rebounds INTEGER,
                    Inside50s INTEGER,
                    Clearances INTEGER,
                    Clangers INTEGER,
                    Frees INTEGER,
                    FreesAgainst INTEGER,
                    BrownlowVotes INTEGER,
                    ContestedPossessions INTEGER,
                    UncontestedPossessions INTEGER,
                    ContestedMarks INTEGER,
                    MarksInside50 INTEGER,
                    OnePercenters INTEGER,
                    Bounces INTEGER,
                    GoalAssists INTEGER,
                    "%Played" INTEGER,
                    Subs TEXT,
                    PRIMARY KEY (PlayerId, GameId),
                    FOREIGN KEY (PlayerId) REFERENCES players(PlayerId),
                    FOREIGN KEY (GameId) REFERENCES games(GameId)
                );

                CREATE INDEX IF NOT EXISTS idx_stats_player ON stats(PlayerId);
                CREATE INDEX IF NOT EXISTS idx_stats_game ON stats(GameId);
                CREATE INDEX IF NOT EXISTS idx_stats_team ON stats(Team);
            """

            try:
                with self.conn.cursor() as cursor:
                      cursor.execute(schema_sql)
                self.conn.commit()
                print("✅ schema created")
            except Exception as e:
                print("❌ Schema creation failed:", e)



    
    def load_data_into_database(self, data: Tuple[List[Any]], col_names: Tuple[List[str]], table_name: str) -> None:
        print("Loading sqlite tables into Postgres database")
        if not data:
            print("No data to insert into table")
            return
        
        cols = ", ".join(col_names)
        insert_query = f"""
            INSERT INTO {table_name} ({cols}) VALUES %s
        """

        with self.conn.cursor() as cursor:
            try:
                execute_values(cursor, insert_query, data)
                self.conn.commit()
                print(f"✅ Inserted {len(data)} rows into '{table_name}'")

            except Exception as e:
                self.conn.rollback()
                print(f"❌ Failed to insert into {table_name}: {e}")

    def clean_game_data(self, games: List[Tuple]):
        # attendance contains and comma. remove it so that i can add the data to the postgres db
        clean_games = []
        for row in games:
            row = list(row)
            print(row[9])
            raw_att = row[9]

            if isinstance(raw_att, str):
                int_att = int(raw_att.replace(",", ""))
                row[9] = int_att
            clean_games.append(tuple(row))

        return clean_games
    
    def rename_col(self, col_name: str, new_col_name: str):
        with self.conn.cursor() as cursor:
            try:
                query = f"""
                    ALTER TABLE stats
                    RENAME COLUMN "{col_name}" TO {new_col_name};
                """

                cursor.execute(query)
                self.conn.commit()
            except Exception as e:
                print(f"Query failed: {e}")

    
    def insert_player_stats(self, player_stats_dto: List[PlayerMatchStatsDTO]):
        if not player_stats_dto:
            return
        
        rows = [dto.model_dump(by_alias=True) for dto in player_stats_dto]
        keys = rows[0].keys()
        placeholders = ", ".join([r"%s"] * len(keys))
        columns = ", ".join(keys)

        query = f"""
            INSERT INTO stats 
            ({columns}) VALUES ({placeholders})
            ON CONFLICT (GameId, PlayerId) DO NOTHING
        """
        
        values = [row.values for row in rows]

        try:
            with self.conn.cursor() as cursor:
                execute_batch(cursor, query, values)
            print(f"✅ Inserted {len(rows)} rows to the stats table")
            self.conn.commit()
        
        except Exception as e:
            print(f"❌ Failed to add rows: {e}")
            self.conn.rollback()

    def insert_game_data(self, games_dto: List[GameDTO]):
        if not games_dto:
            return
        
        


    def check_player_exists(self, display_name: str, dob: str):
        cursor = self.conn.cursor()
        query = r"""
            SELECT PlayerId FROM players
            WHERE DisplayName ILIKE %s AND Dob ILIKE %s
            LIMIT 1
        """
        cursor.execute(query, (display_name, dob))
        row = cursor.fetchone()

        return row[0] if row else None
        
    # def convert_player_ids_to_random_numeric_ids(self):
    #     with sqlite3.connect("afl_stats.db") as conn:
    #         cursor = conn.cursor()
    #         query = """
    #             SELECT PlayerId FROM players
    #         """
    #         all_player_ids = cursor.execute(query)
            
    #         new_ids = {}
    #         for player_id in all_player_ids:
    #             new_id = generate_custom_id()


        

if __name__ == "__main__":
    db = Database(config=load_config())
