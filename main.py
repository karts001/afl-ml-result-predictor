import time
import asyncio
from typing import Tuple

from database import AsyncDatabaseConnection
from dtos.games_dto import GameDTO
from repositories.game_repository import GameRepository
from repositories.player_repository import PlayerRepository
from repositories.stats_repository import StatRepository
from scrapers.afl_tables_scraper import AflTablesScraper
from scrapers.footy_wire_scraper import FootyWireScraper
from services.game_service import GameService
from services.player_service import PlayerService
from services.stat_service import StatService
from logger import logger


def initialise_repositories(db_manager: AsyncDatabaseConnection) -> Tuple[GameRepository, PlayerRepository, StatRepository]:
    """Initialise the game, player and stat repository

    Returns:
        Tuple[GameRepository, PlayerRepository, StatRepository]: Return a tuple containing the
        repositories.
    """
    logger.info("Initialising repositories...")
    game_repository = GameRepository(db_manager)
    player_repository = PlayerRepository(db_manager)
    stat_repository = StatRepository(db_manager)

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
    logger.info("Initialising services...")
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
    logger.info("Initialising scrapers...")
    footy_wire_scraper = FootyWireScraper("https://www.footywire.com/afl/footy")
    afl_tables_scraper = AflTablesScraper(
        base_url="https://afltables.com/afl/stats/",
        game_service=game_service,
        player_service=player_service,
        stat_service=stat_service,
        footy_wire_scraper=footy_wire_scraper,
    )

    return afl_tables_scraper

async def scrape_data_from_afl_tables(afl_tables_scraper: AflTablesScraper) -> Tuple[set, set, set]:
    """Scrape the data from afl tables and footy wire and store in sets

    Args:
        afl_tables_scraper (AflTablesScraper): Scraper object

    Returns:
        Tuple[set, set, set]: Sets for each table in the db
    """
    year = 2025
    match_links = await afl_tables_scraper.get_match_links(year=year)
    game_dtos = set()
    stat_dtos = set()
    player_dtos = set()

    async def process_match(link):
        game_dto = await afl_tables_scraper.get_match_related_data(link)
        if isinstance(game_dto, GameDTO):
            afl_tables_scraper.scraped_games.add(game_dto)
        
        await afl_tables_scraper.get_player_stats_for_match(
            match_endpoint=link,
            game_id=game_dto.game_id, 
            home_team=game_dto.home_team, 
            away_team=game_dto.away_team,
            round_id = game_dto.round_id,
            player_match_stats_dtos=stat_dtos
        )

        return game_dto, player_stat_dtos, player_dtos

    tasks = [process_match(link) for link in match_links]
    results = await asyncio.gather(*tasks)

    for game_dto, player_stat_dtos, player_dtos in results:
        if isinstance(game_dto, GameDTO):
            game_dtos.add(game_dto)
        stat_dtos.update(player_stat_dtos)
        player_dtos.update(player_dtos)
    
    return game_dtos, player_dtos, stat_dtos

async def scrape_stats():
    db_manager = AsyncDatabaseConnection()
    game_repository, player_repository, stat_repository = initialise_repositories(db_manager)
    game_service, player_service, stat_service = initialise_services(
        game_repository, 
        player_repository, 
        stat_repository
    )
    afl_tables_scraper = initialise_scrapers(game_service, player_service, stat_service)
    game_dtos, player_dtos, stat_dtos = await scrape_data_from_afl_tables(afl_tables_scraper) 
    
    await game_service.insert_games(game_dtos)
    await player_service.insert_players(player_dtos)
    await stat_service.insert_stats(stat_dtos)
    

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(scrape_stats())
    print(f"Program took {time.time() - start_time} seconds to complete")
