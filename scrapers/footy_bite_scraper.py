"""Scrape footy wire website to get afl stats data for the 2025 season"""

from typing import List, Tuple
import requests
from bs4 import BeautifulSoup

from scrapers.iscraper import IScraper

class FootyWireScraper(IScraper):
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_match_links(self, year: int = 2025) -> List[str]:
        """
        Scrapes the match list page for a specific round/year and returns game IDs (match codes)

        Args:
            year (int, optional): year to scrape website for. Defaults to 2025.
            round_num (int, optional): the round to website for. Defaults to 1.
        """

        endpoint = f"ft_match_list?year={year}"

        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # rounds are listed as links at the top of the page
        links = soup.find_all("a", href=True)

        return [link["href"] for link in links if "ft_match_statistics" in link["href"]]
    
    def get_match_related_data(soup: BeautifulSoup) -> Tuple[str]:
        round_metadata = soup.find("td", attrs={"class": "lnorm"}).get_text(strip=True)
        round_info = round_metadata.split(",")

        match_round = round_info[0].split(" ")[1] # Get the round no. from the string
        venue = round_info[1]
        attendance = round_info[2]

        return match_round, venue, attendance
    
    def get_player_stats_for_match(self, match_endpoint: str):
        """For a given match get the individual player statistics from the match

        Args:
            match_endpoint (str): url string which denotes the specific endpoint to be used by the 
        """
        response = requests.get(f"{self.base_url}/{match_endpoint}")
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        match_metadata = self.get_match_related_data(soup)

        table = soup.find(id="match-statistics-team1-row")
        
        stats_table = table.find("table", attrs={"cellpadding": "3"})
        header_cells = stats_table.find("tr").find_all("td")

        headers = [header.get_text(strip=True) for header in header_cells]

        data_rows = stats_table.find_all("tr")[1:]

        for row in data_rows:
            cols = row.find_all("td")
            if not cols:
                continue

            player_name = cols[0].find("a").get_text(strip=True)
            if not player_name:
                continue
        
        # TO BE COMPLETED
        # FOOTYBITE WEBSITE DOES NOT PROVIDE ALL OF THE STATS I REQUIRE


if __name__ == "__main__":
    scraper = FootyWireScraper(base_url="https://www.footywire.com/afl/footy")
    match_links = scraper.get_match_links()
    for match in match_links:
        scraper.get_player_stats_for_match(match)