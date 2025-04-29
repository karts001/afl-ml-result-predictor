from typing import List
from dtos.player_profile_dto import PlayerProfileDTO
from repositories.base_repository import BaseRepository


class PlayerRepository(BaseRepository):
    def check_player_exists(self, display_name: str, dob: str):
        query = """
            SELECT *
            FROM players
            WHERE DisplayName ILIKE %s AND Dob = %s
            LIMIT 1
        """
        return self.fetch_one(query, (display_name, dob,))
    
    def insert_players(self, player_dtos: List[PlayerProfileDTO]):
        if not player_dtos:
            return
        
        columns, placeholders, values = self.get_columns_placeholders_and_values(player_dtos)

        query = f"""
            INSERT INTO players
            ({columns}) VALUES ({placeholders})
            ON CONFLICT (PlayerId) DO NOTHING
        """

        self.execute_batch(query, values) 