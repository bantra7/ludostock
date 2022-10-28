import os
from fastapi import Depends, FastAPI
from typing import List
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/games", response_model=List[schemas.Game])
async def get_games(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    games = crud.get_games(db, skip=skip, limit=limit)
    return games


@app.post("/games", response_model=schemas.Game)
async def create_game(game: schemas.CreateGame, db: Session = Depends(get_db)):
    return crud.create_game(db=db, game=game)
