from pydantic import BaseModel, Field

class PlayerProfileDTO(BaseModel):
    player_id: str = Field(alias="PlayerId")
    display_name: str = Field(alias="DisplayName")
    height: int = Field(alias="Height")
    weight: int = Field(alias="Weight")
    dob: str = Field(alias="Dob")
    position: str = Field(alias="Position")
    origin: str = Field(alias="Origin")

    class Config:
        validate_by_name = True
    
