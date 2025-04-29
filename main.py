from config import load_config
from database import Database
from repositories.game_repository import GameRepository
from repositories.player_repository import PlayerRepository
from repositories.stats_repository import StatRepository
from scrapers.afl_tables_scraper import AflTablesScraper
from scrapers.footy_wire_scraper import FootyWireScraper
from services.game_service import GameService
from services.player_service import PlayerService
from services.stat_service import StatService


def scrape_stats():
    # create repositories
    game_repository = GameRepository()
    player_repository = PlayerRepository()
    stat_repository = StatRepository()
    # create services
    game_service = GameService(game_repository)
    player_service = PlayerService(player_repository)
    stat_service = StatService(stat_repository)

    # create scrapers
    footy_wire_scraper = FootyWireScraper("https://www.footywire.com/afl/footy")
    afl_tables_scraper = AflTablesScraper(
        base_url="https://afltables.com/afl/stats",
        game_service=game_service,
        player_service=player_service,
        stat_service=stat_service,
        footy_wire_scraper=footy_wire_scraper
    )

    match_links = afl_tables_scraper.get_match_links()
    game_dtos = set()
    stat_dtos = set()
    player_dtos = set()

    for link in match_links:
        game_dto = afl_tables_scraper.get_match_related_data(link)
        player_stat_dtos, player_profile_dtos = afl_tables_scraper.get_player_stats_for_match(
            match_endpoint=link,
            game_id=game_dto.game_id, 
            home_team=game_dto.home_team, 
            away_team=game_dto.away_team,
            round_id = game_dto.round_id
        )
        game_dtos.add(game_dto)
        stat_dtos.update(player_stat_dtos)
        player_dtos.update(player_profile_dtos)
    
    game_service.insert_games(game_dtos)
    player_service.insert_players(player_dtos)
    stat_service.insert_stats(stat_dtos)


if __name__ == "__main__":
    scrape_stats()


