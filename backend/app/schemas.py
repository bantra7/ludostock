from pydantic import BaseModel
from typing import List, Optional # Added List and Optional

# Label Schemas
class LabelBase(BaseModel):
    name: str

    # It's good practice to have orm_mode here if it's consistently used,
    # but Pydantic v2 inherits it effectively.
    # For clarity with the request, I'll ensure the main response model (Label) has it.

class LabelCreate(LabelBase):
    pass

class Label(LabelBase):
    id: int

    class Config:
        orm_mode = True

# BoardGame Schemas
class BoardGameBase(BaseModel):
    name: str # Renamed from title
    editor_name: str
    num_players_min: int
    num_players_max: int
    age_min: int
    time_duration_mean: Optional[int] = None # Updated field

    class Config:
        orm_mode = True

class BoardGameCreate(BoardGameBase):
    labels: List[str] = [] # List of label names, using typing.List

class BoardGame(BoardGameBase):
    id: int
    labels: List[Label] = [] # Nested Label schemas, using typing.List

    # Config orm_mode is inherited from BoardGameBase, so not strictly needed here
    # but can be explicit if preferred. The example shows it omitted here, so I will follow that.
