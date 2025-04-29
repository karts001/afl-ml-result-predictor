from typing import List
from dtos.player_profile_dto import PlayerProfileDTO
from repositories.player_repository import PlayerRepository


class PlayerService():
    def __init__(self, repo: PlayerRepository):
        self.repo = repo

    def check_if_player_exists(self, display_name: str, dob: str) -> bool:
        return self.repo.check_player_exists(display_name, dob)

    def insert_players(self, player_dtos: List[PlayerProfileDTO]) -> None:
        self.repo.insert_games(player_dtos)
