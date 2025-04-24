from config import load_config
from database import Database
from scrapers.afl_tables_scraper import AflTablesScraper
from scrapers.footy_wire_scraper import FootyWireScraper

def scrape_stats():
    scraper = AflTablesScraper(base_url="https://afltables.com/afl/stats")
    match_links = scraper.get_match_links()

    for link in match_links:
        match_data = scraper.get_match_related_data(link)
        player_stats = scraper.get_player_stats_for_match(link)

if __name__ == "__main__":
    afl_table_scraper = AflTablesScraper(base_url="https://afltables.com/afl/stats")
    footy_bite_scraper = FootyWireScraper(base_url="https://www.footywire.com/afl/footy")
    db = Database(config=load_config())
    
    match_links = afl_table_scraper.get_match_links()

    game_dtos = []
    player_dtos = []
    stats_dtos = []
    for game_index, link in enumerate(match_links, start=1):
        game_dto, game_id = afl_table_scraper.get_match_related_data(link, game_index)
        player_stats_dto = afl_table_scraper.get_player_stats_for_match(link, game_id)
        

    db.insert_games(game_dtos)

