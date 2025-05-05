from typing import List

from repositories.base_repository import BaseRepository
from dtos.games_dto import GameDTO

class GameRepository(BaseRepository): 
    def check_game_exists(self, date: str, home_team: str, away_team: str) -> bool:
        query = """
            SELECT 1
            FROM games
            WHERE Date = %s AND HomeTeam = %s AND AwayTeam = %s
            LIMIT 1
        """
        result = self.fetch_one(query, (date, home_team, away_team))

        return result is not None

    def insert_games(self, game_dtos: List[GameDTO]) -> None:
        if not game_dtos:
            return
        
        columns, placeholders, values = self.get_columns_placeholders_and_values(game_dtos)

        query = f"""
            INSERT INTO games
            ({columns}) VALUES ({placeholders})
            ON CONFLICT (GameId) DO NOTHING
        """
        self.execute_batch(query, values)
        