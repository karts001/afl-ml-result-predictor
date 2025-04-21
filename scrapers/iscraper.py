from abc import ABC, abstractmethod
from typing import List, Tuple

class IScraper(ABC):
    @abstractmethod
    def get_match_links(self) -> List[str]:
        pass

    @abstractmethod
    def get_match_related_data(self) -> Tuple[str]:
        pass

    @abstractmethod
    def get_player_stats_for_match(self, match_endpoint: str):
        pass