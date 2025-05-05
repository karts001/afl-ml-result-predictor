import time

from typing import Tuple
from psycopg2.extensions import connection as Connection

from config import load_config
from database import DatabaseConnectionManager
from dtos.player_profile_dto import PlayerProfileDTO
from repositories.game_repository import GameRepository
from repositories.player_repository import PlayerRepository
from repositories.stats_repository import StatRepository
from scrapers.afl_tables_scraper import AflTablesScraper
from scrapers.footy_wire_scraper import FootyWireScraper
from services.game_service import GameService
from services.player_service import PlayerService
from services.stat_service import StatService

def initialise_repositories(conn: Connection) -> Tuple[GameRepository, PlayerRepository, StatRepository]:
    """Initialise the game, player and stat repository

    Returns:
        Tuple[GameRepository, PlayerRepository, StatRepository]: Return a tuple containing the
        repositories.
    """
    game_repository = GameRepository(conn)
    player_repository = PlayerRepository(conn)
    stat_repository = StatRepository(conn)

    return game_repository, player_repository, stat_repository

def initialise_services(
        game_repository: GameRepository, 
        player_repository: PlayerRepository, 
        stat_repository: StatRepository
) -> Tuple[GameService, PlayerService, StatService]:
    """Initialise game, player and stat services

    Args:
        game_repository (GameRepository): Game repository used by the game service
        player_repository (PlayerRepository): Player repository used by the player service
        stat_repository (StatRepository): Player repository used by the player service

    Returns:
        Tuple[GameService, PlayerService, StatService]: Tuple containing the services
    """
    game_service = GameService(game_repository)
    player_service = PlayerService(player_repository)
    stat_service = StatService(stat_repository)

    return game_service, player_service, stat_service

def initialise_scrapers(
        game_service: GameService,
        player_service: PlayerService, 
        stat_service: StatService,
) -> AflTablesScraper:
    """Initalise the afl tables and footy wire scrapers

    Args:
        game_service (GameService): Initialisation requires this service
        player_service (PlayerService): Initialisation requires this service
        stat_service (StatService): Initialisation requires this service

    Returns:
        AflTablesScraper: The scraper class
    """
    # create scrapers
    footy_wire_scraper = FootyWireScraper("https://www.footywire.com/afl/footy")
    afl_tables_scraper = AflTablesScraper(
        base_url="https://afltables.com/afl/stats/",
        game_service=game_service,
        player_service=player_service,
        stat_service=stat_service,
        footy_wire_scraper=footy_wire_scraper,
    )

    return afl_tables_scraper

def scrape_data_from_afl_tables(afl_tables_scraper: AflTablesScraper) -> Tuple[set, set, set]:
    """Scrape the data from afl tables and footy wire and store in sets

    Args:
        afl_tables_scraper (AflTablesScraper): Scraper object

    Returns:
        Tuple[set, set, set]: Sets for each table in the db
    """
    match_links = afl_tables_scraper.get_match_links(year=2025)
    game_dtos = set()
    stat_dtos = set()
    player_dtos = set()

    for link in match_links:
        game_dto = afl_tables_scraper.get_match_related_data(link)
        player_stat_dtos, player_dtos = afl_tables_scraper.get_player_stats_for_match(
            match_endpoint=link,
            game_id=game_dto.game_id, 
            home_team=game_dto.home_team, 
            away_team=game_dto.away_team,
            round_id = game_dto.round_id,
            player_dtos=player_dtos,
            player_match_stats_dtos=stat_dtos
        )
        game_dtos.add(game_dto)
        stat_dtos.update(player_stat_dtos)
        player_dtos.update(player_dtos)
    
    return game_dtos, player_dtos, stat_dtos

def scrape_stats():
    db_manager = DatabaseConnectionManager(load_config())
    game_repository, player_repository, stat_repository = initialise_repositories(db_manager)
    game_service, player_service, stat_service = initialise_services(
        game_repository, 
        player_repository, 
        stat_repository
    )
    afl_tables_scraper = initialise_scrapers(game_service, player_service, stat_service)
    game_dtos, player_dtos, stat_dtos = scrape_data_from_afl_tables(afl_tables_scraper) 
    
    game_service.insert_games(game_dtos)
    player_service.insert_players(player_dtos)
    stat_service.insert_stats(stat_dtos)
    

if __name__ == "__main__":
    start_time = time.time()
    scrape_stats()
    print(f"Program took {time.time() - start_time} seconds to complete")
