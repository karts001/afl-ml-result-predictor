import re

from typing import List
import requests
from bs4 import BeautifulSoup

from dtos.games_dto import MatchMetadataDTO, MatchScoreDTO
from scrapers.iscraper import IScraper


class AflTablesScraper(IScraper):
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_match_links(self, year: int = 2025) -> List[str]:
        print("Getting a list of endpoints which refer to stats from specific games")
        response = requests.get(f"{self.base_url}/{year}t.html")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        all_links = soup.find_all("a", href=True)
        return list(set(link["href"] for link in all_links if f"games/{year}" in link["href"]))

    def get_match_metadata(self, match_endpoint: str):
        response = requests.get(f"{self.base_url}/{match_endpoint}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        full_table = soup.find("table")
        all_rows = full_table.find_all("tr")

        metadata_string = all_rows[0].find("td", attrs={"align": "center"}).get_text(strip=True)

        # string returned is not in a useful format. Use a regex expression to extract the required data
        pattern = r"Round:(\d+)Venue:(.*?)Date:.*?(\d{2}-\w{3}-\d{4}) (\d{1,2}:\d{2} [APM]+).*?Attendance:(\d+)"
        match = re.search(pattern, metadata_string)

        if match:
            metadata_dto = MatchMetadataDTO(
                round_id = int(match.group(1)),
                venue = match.group(2).strip(),
                date = match.group(3),
                time = match.group(4),
                attendance = int(match.group(5))
            )

        remaining_rows = all_rows[1:3]

        home_team, away_team = None, None
        home_scores, away_score = {}, {}              

        for row_index, row in enumerate(remaining_rows):
            cells = row.find_all("td")
            team = cells[0].get_text(strip=True)

            qt = self._before_second_dot(cells[1].get_text(strip=True))
            ht = self._before_second_dot(cells[2].get_text(strip=True))
            tqt = self._before_second_dot(cells[3].get_text(strip=True))
            ft = self._before_second_dot(cells[4].get_text(strip=True))
            final_score = cells[4].get_text(strip=True).split(".")[2]


            scores = {
                "qt": qt,
                "ht": ht,
                "3qt": tqt,
                "ft": ft,
                "final_score": final_score
            }

            if row_index == 0:
                home_team = team
                home_scores = scores
            if row_index == 1:
                away_team = team
                away_scores = scores

        print("something")

        match_scores_dto = MatchScoreDTO(
            home_team=home_team,
            home_team_score_qt=home_scores.get("qt"),
            home_team_score_ht=home_scores.get("ht"),
            home_team_score_3qt=home_scores.get("3qt"),
            home_team_score_ft=home_scores.get("ft"),
            home_team_score=home_scores.get("final_score"),
            away_team=away_team,
            away_team_score_qt=away_scores.get("qt"),
            away_team_score_ht=away_scores.get("ht"),
            away_team_score_3qt=away_scores.get("3qt"),
            away_team_score_ft=away_scores.get("ft"),
            away_team_score=away_scores.get("final_score") 
        )

        return (metadata_dto, match_scores_dto)

    def _before_second_dot(self, value: str) -> str:
        parts = value.split(".")
        return ".".join(parts[:2]) if len(parts) >= 2 else value

    def get_player_stats_for_match(self, match_endpoint):
        pass


if __name__ == "__main__":
    scraper = AflTablesScraper(base_url="https://afltables.com/afl/stats")
    match_links = scraper.get_match_links()

    for link in match_links:
        match_data = scraper.get_match_metadata(link)
        print(match_data)