from pydantic import BaseModel

class GameBase(BaseModel):
    title: str

    class Config:
        orm_mode = True


class Game(GameBase):
    game_id: int

    class Config:
        orm_mode = True


class CreateGame(GameBase):
    pass