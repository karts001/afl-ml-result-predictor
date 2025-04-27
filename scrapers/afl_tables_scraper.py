import re
from urllib.parse import urljoin
from collections import defaultdict

from typing import List, Tuple
import requests
from bs4 import BeautifulSoup, ResultSet

from config import load_config
from database import Database
from dtos.games_dto import GameDTO, MatchMetadataDTO, MatchScoreDTO
from dtos.player_profile_dto import PlayerProfileDTO
from dtos.stats_dto import PlayerMatchStatsDTO
from helpers import field_names
from scrapers.footy_wire_scraper import FootyWireScraper


class AflTablesScraper():
    def __init__(self, base_url: str, db: Database, footy_wire_scraper: FootyWireScraper):
        self.base_url = base_url
        self.db = db # use to check whether a player already exists in the player table
        self.footy_wire_scraper = footy_wire_scraper
        self.game_index_counter = defaultdict(int)

    def get_match_links(self, year: int = 2025) -> List[str]:
        """Get a list of endpoints which refer to specific match stats for a given year

        Args:
            year (int, optional): Year of data to scrape. Defaults to 2025.

        Returns:
            List[str]: A list of endpoints which correspond to matches which have occured
            in that year.
        """
        print("Getting a list of endpoints which refer to stats from specific games")
        response = requests.get(f"{self.base_url}{year}t.html")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        all_links = soup.find_all("a", href=True)

        return list(dict.fromkeys(
            link["href"] for link in all_links if f"games/{year}" in link["href"]
        ))

    def get_match_related_data(self, match_endpoint: str) -> Tuple[GameDTO, str]:
        """Get metadata and score data related to a specific match

        Args:
            match_endpoint (str): endpoint which refers to a specific match
            game_index (int): Number of the game in the round

        Returns:
            Tuple[MatchMetadataDTO, MatchScoreDTO]: Tuple containing the match related data
        """
        print("Getting game related data")
        response = requests.get(f"{self.base_url}{match_endpoint}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        full_table = soup.find("table")
        all_rows = full_table.find_all("tr")

        metadata_dto, game_id = self._get_match_metadata(all_rows, game_index)    
        match_scores_dto = self._get_match_score_data(all_rows)
        game_dto = GameDTO(**metadata_dto.model_dump(), **match_scores_dto.model_dump())

        return (game_dto, game_id)
    
    def _get_match_metadata(self, all_rows: ResultSet) -> Tuple[MatchMetadataDTO, str]:
        """Scrape metadata of a specific match from afl tables website

        Args:
            all_rows (ResultSet): A collection of all of the rows from the HTML table containing the metadata

        Returns:
            MatchMetadataDTO: DTO which holds the relevant match related data
        """

        print("Getting match metadata (i.e. Attendance, Venue, etc.)")
        metadata_string = all_rows[0].find("td", attrs={"align": "center"}).get_text(strip=True)

        # string returned is not in a useful format. Use a regex expression to extract the required data
        pattern = r"Round:(\d+)Venue:(.*?)Date:.*?(\d{1,2}-\w{3}-\d{4}) (\d{1,2}:\d{2} [AP]M).*?Attendance:(\d+)"
        # FIXME: Pattern only works for rounds like R1,R2.. R23, but it won't work for Quarter finals etc.
        match = re.search(pattern, metadata_string)
        
        if match:
            round = match.group(1) # get the round from the string
            year = match.group(3).split("-")[2] # get the year from the string

            # increment the game index counter
            self.game_index_counter[round] += 1
            game_index = self.game_index_counter[round]

            # Build the game id string
            game_id = f"{year}R{int(match.group(1)):02d}{game_index:02d}"

            metadata_dto = MatchMetadataDTO(
                game_id = game_id,
                year=year,
                round_id = round,
                venue = match.group(2).strip(),
                date = match.group(3),
                start_time = match.group(4),
                attendance = int(match.group(5))
            )
        else:
            print(f"{metadata_string}")

        return metadata_dto, game_id
    
    def _get_match_score_data(self, all_rows: ResultSet) -> MatchScoreDTO:
        """Get the data related to the match score from the afl tables website

        Args:
            all_rows (ResultSet): A collection of all of the rows from the HTML table containing the metadata

        Returns:
            MatchScoreDTO: DTO which holds the relevant match score related data
        """
        remaining_rows = all_rows[1:3] # skip the header row

        teams = []
        scores_list = []

        # loop through rows and get the game score data and store it in the respective list
        for row in remaining_rows:
            cells = row.find_all("td")
            team_name = cells[0].get_text(strip=True)
            print(f"Getting score data for {team_name}")

            # afl scores follow and Goal.Behind.Total format. We just want the first 2
            score_data = [self._before_second_dot(cells[i].get_text(strip=True)) for i in range(1, 5)]
            final_score = cells[4].get_text(strip=True).split(".")[2] # Get the final score of the game

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

    def get_player_stats_for_match(self,
        match_endpoint: str,
        game_id: str,
        home_team: str,
        away_team: str,
        round_id: str
    ) -> Tuple[List[PlayerMatchStatsDTO], List[PlayerProfileDTO]]:
        """Get the individual player stats (Kicks, Disposals etc.) for a given match

        Args:
            match_endpoint (str): The url which contains stats for the given match
            game_id (str): GameId referring the given match
            home_team (str): Name of the home team
            away_team (str): Name of the away team
            round_id (str): RoundId for the given match

        Returns:
            Tuple[List[PlayerMatchStatsDTO], List[PlayerProfileDTO]]: Tuple containing a list 
            of the PlayerMatchStatsDTO and a list of PlayerProfileDTO
        """
        print(f"Getting player stats for game: {game_id} and round: {round_id}")
        response = requests.get(f"{self.base_url}{match_endpoint}")
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get all tables with class 'sortable' and Match Statistics in the header
        sortable_tables = soup.find_all("table", class_="sortable")
        match_stats_tables = [table for table in sortable_tables if "Match Statistics" in table.find("th").get_text(strip=True)]     

        players_stats_dtos = []
        players_profile_dtos = []

        for index, table in enumerate(match_stats_tables):
            rows = table.find_all("tr")[2:]  # skip header rows
            for row in rows:
                cells = row.find_all("td") # get all the cells
                if len(cells) < 25:
                    continue  # skip malformed or empty rows
                
                # Get the players name
                player_link = cells[1].find("a")["href"] # url for player profile
                display_name = cells[1].get_text(strip=True)

                # get the D.O.B from the player profile
                dob = self.get_player_dob(player_link)
                # check if the player exists by querying display_name and dob
                player = self.db.check_player_exists(display_name, dob)

                if not player:
                    # if the player does not exist in the database
                    # create a new entry in the players table
                    print(f"Scraping profile data for {display_name}")
                    players_profile_dtos.append(
                        self.footy_wire_scraper.get_player_profile_stats(
                            team_name=home_team if index == 0 else away_team,
                            display_name=display_name
                    ))

                # Map field names to their corresponding int values from cells[2:25]
                # Unpack dictionary to form DTO
                stat_values = {
                    field: int(cells[i + 2].get_text(strip=True) or 0) 
                    for i, field in enumerate(field_names)
                }
                player_stats_dto = PlayerMatchStatsDTO(
                    player_name=display_name,
                    game_id=game_id,
                    team=home_team if index == 0 else away_team,
                    year=2025,
                    round=round_id,
                    **stat_values
                )
                
                players_stats_dtos.append(player_stats_dto)
        
        return (players_stats_dtos, players_profile_dtos)
    
    def get_player_dob(self, player_link: str) -> str:
        """Scrape the date of birth from the html

        Args:
            player_link (str): Endpoint url for given player's profile

        Returns:
            str: Dob as a string
        """

        response = requests.get(urljoin(f"{self.base_url}games/2025/", player_link)) #FIXME: fudged url to work with player_link value
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        born_b_tag = soup.find("b", string=re.compile(r"Born:"))
        # Extract the text that comes after "Born:" and format it
        if born_b_tag:
            # Use regex to extract the date portion
            dob = born_b_tag.next_sibling.replace("(", "").strip()
        else:
            print("DOB not found")

        return dob
    

if __name__ == "__main__":
    footy_wire_scraper = FootyWireScraper(base_url="https://www.footywire.com/afl/footy")
    db = Database(config=load_config())
    scraper = AflTablesScraper(
        base_url="https://afltables.com/afl/stats/",
        footy_wire_scraper=footy_wire_scraper,
        db=db
    )
    match_links = scraper.get_match_links()

    game_dtos = []

    for link in match_links:
        game_dto, game_id = scraper.get_match_related_data(link)
        players_stats, players_identity_data = scraper.get_player_stats_for_match(
            match_endpoint=link,
            game_id=game_id, 
            home_team=game_dto.home_team, 
            away_team=game_dto.away_team,
            round_id = game_dto.round_id
        )
        game_dtos.append(game_dto)

    print(len(game_dtos))
    print(len(players_identity_data))
    print(len(players_stats))
