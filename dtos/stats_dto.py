from pydantic import BaseModel

class PlayerMatchStatsDTO(BaseModel):
    player_name: str
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
    free_kicks_for: int
    free_kicks_against: int
    rebound50s: int
    inside50s: int
    brownlow_votes: int
    contested_possessions: int
    uncontested_possessions: int
    contested_marks: int
    marks_inside: int
    one_percenters: int
    bounces: int
    goal_assist: int
    percent_played: int
    