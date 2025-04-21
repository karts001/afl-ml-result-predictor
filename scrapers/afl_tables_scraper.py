import re

from typing import List, Tuple
import requests
from bs4 import BeautifulSoup, ResultSet

from dtos.games_dto import MatchMetadataDTO, MatchScoreDTO
from dtos.stats_dto import PlayerMatchStatsDTO
from scrapers.iscraper import IScraper
from helpers import field_names


class AflTablesScraper(IScraper):
    def __init__(self, base_url: str):
        self.base_url = base_url


    def get_match_links(self, year: int = 2025) -> List[str]:
        """Get a list of endpoints which refer to specific match stats for a given year

        Args:
            year (int, optional): Year of data to scrape. Defaults to 2025.

        Returns:
            List[str]: A list of endpoints which correspond to matches which have occured
            in that year.
        """
        print("Getting a list of endpoints which refer to stats from specific games")
        response = requests.get(f"{self.base_url}/{year}t.html")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        all_links = soup.find_all("a", href=True)
        return list(set(link["href"] for link in all_links if f"games/{year}" in link["href"]))

    def get_match_related_data(self, match_endpoint: str) -> Tuple[MatchMetadataDTO, MatchScoreDTO]:
        """Get metadata and score data related to a specific match

        Args:
            match_endpoint (str): endpoint which refers to a specific match

        Returns:
            Tuple[MatchMetadataDTO, MatchScoreDTO]: Tuple containing the match related data
        """
        
        response = requests.get(f"{self.base_url}/{match_endpoint}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        full_table = soup.find("table")
        all_rows = full_table.find_all("tr")

        metadata_dto = self.get_match_metadata(all_rows)    
        match_scores_dto = self.get_match_score_data(all_rows)

        return (metadata_dto, match_scores_dto)
    
    def get_match_metadata(self, all_rows: ResultSet) -> MatchMetadataDTO:
        """Scrape metadata of a specific match from afl tables website

        Args:
            all_rows (ResultSet): A collection of all of the rows from the HTML table containing the metadata

        Returns:
            MatchMetadataDTO: DTO which holds the relevant match related data
        """
        metadata_string = all_rows[0].find("td", attrs={"align": "center"}).get_text(strip=True)

        # string returned is not in a useful format. Use a regex expression to extract the required data
        old_pattern = r"Round:(\d+)Venue:(.*?)Date:.*?(\d{2}-\w{3}-\d{4}) (\d{1,2}:\d{2} [APM]+).*?Attendance:(\d+)"
        pattern = r"Round:(\d+)Venue:(.*?)Date:.*?(\d{1,2}-\w{3}-\d{4}) (\d{1,2}:\d{2} [AP]M).*?Attendance:(\d+)"
        match = re.search(pattern, metadata_string)
        
        if match:
            metadata_dto = MatchMetadataDTO(
                round_id = int(match.group(1)),
                venue = match.group(2).strip(),
                date = match.group(3),
                time = match.group(4),
                attendance = int(match.group(5))
            )
        else:
            print(f"{metadata_string}")

        return metadata_dto
    
    def get_match_score_data(self, all_rows: ResultSet) -> MatchScoreDTO:
        """Get the data related to the match score from the afl tables website

        Args:
            all_rows (ResultSet): A collection of all of the rows from the HTML table containing the metadata

        Returns:
            MatchScoreDTO: DTO which holds the relevant match score related data
        """
        remaining_rows = all_rows[1:3]

        teams = []
        scores_list = []

        for row in remaining_rows:
            cells = row.find_all("td")
            team_name = cells[0].get_text(strip=True)

            score_data = [self._before_second_dot(cells[i].get_text(strip=True)) for i in range(1, 5)]
            final_score = cells[4].get_text(strip=True).split(".")[2]

            teams.append(team_name)
            scores_list.append({
                "qt": score_data[0],
                "ht": score_data[1],
                "3qt": score_data[2],
                "ft": score_data[3],
                "final_score": final_score
            })

        return MatchScoreDTO(
            home_team=teams[0],
            home_team_score_qt=scores_list[0].get("qt"),
            home_team_score_ht=scores_list[0].get("ht"),
            home_team_score_3qt=scores_list[0].get("3qt"),
            home_team_score_ft=scores_list[0].get("ft"),
            home_team_score=scores_list[0].get("final_score"),
            away_team=teams[1],
            away_team_score_qt=scores_list[1].get("qt"),
            away_team_score_ht=scores_list[1].get("ht"),
            away_team_score_3qt=scores_list[1].get("3qt"),
            away_team_score_ft=scores_list[1].get("ft"),
            away_team_score=scores_list[1].get("final_score")
        )

    def _before_second_dot(self, value: str) -> str:
        """Helper function which extracts relevant data from afl tables website.
        Scores from each quarter are listed in the following format G.B.T
        G stands for goals (6 points), B is for Behinds (1 point), and T is the total
        The original kaggle data ommited the total score from each quarter so to keep the data consistent
        I am ommiting it as well.

        Args:
            value (str): quarter score in B.G.T format

        Returns:
            str: score string with total score removed
        """
        parts = value.split(".")
        return ".".join(parts[:2]) if len(parts) >= 2 else value

    def get_player_stats_for_match(self, match_endpoint: str):

        response = requests.get(f"{self.base_url}/{match_endpoint}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get all tables with class 'sortable'
        sortable_tables = soup.find_all("table", class_="sortable")

        match_stats_tables = [table for table in sortable_tables if "Match Statistics" in table.find("th").get_text(strip=True)]        

        players_stats = []
        for table in match_stats_tables:
            rows = table.find_all("tr")[2:]  # skip header rows

            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 25:
                    continue  # skip malformed or empty rows
                
                # Get the players name
                player_name = cells[1].get_text(strip=True)
                # Map field names to their corresponding int values from cells[2:25]
                stat_values = {
                    field: int(cells[i + 2].get_text(strip=True) or 0) 
                    for i, field in enumerate(field_names)
                }

                player_stats_dto = PlayerMatchStatsDTO(
                    **stat_values,
                    player_name=player_name
                )
                
                players_stats.append(player_stats_dto)
        
        return player_stats
                        

if __name__ == "__main__":
    scraper = AflTablesScraper(base_url="https://afltables.com/afl/stats")
    match_links = scraper.get_match_links()

    for link in match_links:
        match_data = scraper.get_match_related_data(link)
        player_stats = scraper.get_player_stats_for_match(link)