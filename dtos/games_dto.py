from pydantic import BaseModel

class MatchMetadataDTO(BaseModel):
    round_id: int
    venue: str
    attendance: int # convert to int before inserting into db?
    date: str
    time: str

class MatchScoreDTO(BaseModel):
    home_team: str
    home_team_score_qt: str
    home_team_score_ht: str
    home_team_score_3qt: str
    home_team_score_ft: str
    home_team_score: str
    away_team: str
    away_team_score_qt: str
    away_team_score_ht: str
    away_team_score_3qt: str
    away_team_score_ft: str
    away_team_score: str

