from typing import List
from dtos.stats_dto import PlayerMatchStatsDTO
from repositories.base_repository import BaseRepository


class StatRepository(BaseRepository):
    def check_stat_exists(self, game_id: str, player_id: str) -> bool:
        query = """
            SELECT 1
            FROM stats
            WHERE GameId ILIKE %s and PlayerId ILIKE %s
            LIMIT 1
        """
        return self.fetch_one(query, (game_id, player_id))
    
    def insert_stats(self, stat_dtos: List[PlayerMatchStatsDTO]) -> None:
        if not stat_dtos:
            return
        
        columns, placeholders, values = self.get_columns_placeholders_and_values(stat_dtos)
        
        query = f"""
            INSERT INTO games
            ({columns}) VALUES ({placeholders})
            ON CONFLICT (GameId, PlayerId) DO NOTHING
        """
        self.execute_batch(query, values)