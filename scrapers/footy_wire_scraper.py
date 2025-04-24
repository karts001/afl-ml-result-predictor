"""Scrape footy wire website to get afl stats data for the 2025 season"""

import re
from typing import Tuple

import requests
from bs4 import BeautifulSoup
from nanoid import generate

from dtos.player_profile_dto import PlayerProfileDTO

class FootyWireScraper():
    def __init__(self, base_url: str):
        self.base_url = base_url

    def get_player_profile_stats(
        self,
        display_name: str,
        team_name: str,
    ) -> PlayerProfileDTO:
        
        team_name_split = team_name.split()
        if len(team_name_split) > 1:
            team_name = "-".join(team_name_split)
            print(team_name)
        
        player_name = self.convert_display_name(display_name)
        url = f"{self.base_url}/pp-{team_name.lower()}--{player_name.lower()}"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        if "Oops! Player Not Found ..." in soup.get_text(strip=True):
            print(f"Can't find {player_name} in FootyWire")
            print(f"Tried scraping the following url: {url}")
            return
        
        profile_str = soup.find("div", id="playerProfileData1").get_text(strip=True)
        dob, origin = self.extract_identity_data(profile_str)     

        biometrics_str = soup.find("div", id="playerProfileData2").get_text(strip=True)
        height, weight, position = self.extract_biometric_data(biometrics_str)

        return PlayerProfileDTO(
            player_id=generate(size=10),
            display_name=display_name,
            dob=dob,
            height=height,
            weight=weight,
            position=position,
            origin=origin
        )
    
    def convert_display_name(self, name: str):
        # Split the name into "Last" and "First [Middle]"
        parts = name.split(",")
        if len(parts) != 2:
            raise ValueError("Name must be in 'Last, First' format")

        last = parts[0].strip()
        first_and_middle = parts[1].strip().split()

        # Reassemble in First-Middle-Last format
        reordered = first_and_middle + [last]
        return "-".join(reordered)

    def extract_identity_data(self, input_str: str) -> Tuple[str, str]:
        dob_match = re.search(r'Born:\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})', input_str)
        origin_match = re.search(r'Origin:\s+(.+)', input_str)

        dob = dob_match.group(1) if dob_match else None
        origin = origin_match.group(1).strip() if origin_match else None

        return dob, origin
    
    def extract_biometric_data(self, input_str: str) -> Tuple[int, int, str]:
        height_match = re.search(r'Height:\s*(\d+)\s*cm', input_str)
        weight_match = re.search(r'Weight:\s*(\d+)\s*kg', input_str)

        height = int(height_match.group(1)) if height_match else None
        weight = int(weight_match.group(1)) if weight_match else None
        
        position_section = re.search(r'Position:\s*(.*)', input_str, re.DOTALL)
        
        if position_section:
            raw_positions = position_section.group(1)
            positions = [pos.strip() for pos in raw_positions.replace("\n", "").split(",")]
            position_str = ", ".join(positions)
        else:
            position_str = None

        return height, weight, position_str     


if __name__ == "__main__":
    scraper = FootyWireScraper(base_url="https://www.footywire.com/afl/footy")
    player_profile_dto = scraper.get_player_profile_stats("windsor, caleb", "melbourne")