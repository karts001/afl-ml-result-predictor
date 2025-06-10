from typing import List

from repositories.base_repository import BaseRepository
from dtos.games_dto import GameDTO

from logger import logger

class GameRepository(BaseRepository): 
    async def check_game_exists(self, date: str, home_team: str, away_team: str) -> bool:
        query = """
            SELECT 1
            FROM games
            WHERE Date = $1 AND HomeTeam = $2 AND AwayTeam = $3
            LIMIT 1
        """
        logger.info(f"date: {date}, home_team: {home_team}, away_team: {away_team}")
        result = await self.fetch_one(query, (date, home_team, away_team))

        return result is not None

    async def insert_games(self, game_dtos: List[GameDTO]) -> None:
        if not game_dtos:
            return
        
        columns, placeholders, values = self.get_columns_placeholders_and_values(game_dtos)

        query = f"""
            INSERT INTO games
            ({columns}) VALUES ({placeholders})
            ON CONFLICT (GameId) DO NOTHING
        """
        await self.execute_batch(query, values)
        