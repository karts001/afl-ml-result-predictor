from pydantic import BaseModel

class PlayerMatchStatsDTO(BaseModel):
    kicks: int
    marks: int
    handballs: int
    disposals: int
    goals: int
    behinds: int
    tackles: int
    hitouts: int
    inside50s: int
    clearances: int
    clangers: int
    frees: int
    frees_against: int
    rebounds: int
    