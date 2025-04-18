import pandas as pd
import sqlite3
from sqlite3 import Connection

def create_database_schema() -> Connection:
    # connect to database and add dataframes to a database while ignore the index
    print("Connecting to DB and creating the schema")
    with sqlite3.connect("afl_stats.db") as conn:
        cursor = conn.cursor()

        schema_sql = """
            CREATE TABLE IF NOT EXISTS players (
                PlayerId INTEGER PRIMARY KEY,
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
                PlayerId INTEGER,
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

        cursor.executescript(schema_sql)
        # enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

        return conn

def load_csv_files_into_database(conn: Connection):
    # load csv files as dataframes
    df_games = pd.read_csv("kaggle_data/games.csv")
    df_players = pd.read_csv("kaggle_data/players.csv")
    df_stats = pd.read_csv("kaggle_data/stats.csv")
        
    df_games.to_sql("games", index=False, con=conn, if_exists="append")
    df_players.to_sql("players", index=False, con=conn, if_exists="append")
    df_stats.to_sql("stats", index=False, con=conn, if_exists="append")

def init_db():
    conn = create_database_schema()
    load_csv_files_into_database(conn)

if __name__ == "__main__":
    init_db()
