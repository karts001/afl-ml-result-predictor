from typing import List
from dtos.games_dto import GameDTO
from repositories.game_repository import GameRepository


class GameService():
    def __init__(self, repo: GameRepository):
        self.repo = repo

    def check_if_game_exists(self, date: str, home_team: str, away_team: str) -> bool:
        return self.repo.check_game_exists(date, home_team, away_team)

    def insert_games(self, game_dtos: List[GameDTO]) -> None:
        self.repo.insert_games(game_dtos)
