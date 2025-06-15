import os
from fastapi import Depends, FastAPI, HTTPException # Added HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from sqlalchemy.orm import Session
from . import crud, models, schemas # models.Base will be accessed via this
from .database import SessionLocal, engine # engine is here

# This line ensures that all tables are created based on models.
# It should be called after all models are defined (which happens when `models` is imported)
models.Base.metadata.create_all(bind=engine) # Commented out to prevent execution during test collection

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows specific origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Label Endpoints
@app.post("/api/labels/", response_model=schemas.Label, tags=["Labels"])
async def create_label_endpoint(label: schemas.LabelCreate, db: Session = Depends(get_db)):
    db_label = crud.get_label_by_name(db, name=label.name)
    if db_label:
        raise HTTPException(status_code=400, detail="Label with this name already exists")
    return crud.create_label(db=db, label=label)

@app.get("/api/labels/", response_model=List[schemas.Label], tags=["Labels"])
async def get_labels_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    labels = crud.get_labels(db, skip=skip, limit=limit)
    return labels

@app.get("/api/labels/{label_name}", response_model=schemas.Label, tags=["Labels"])
async def get_label_endpoint(label_name: str, db: Session = Depends(get_db)): # Changed label_id to label_name
    db_label = crud.get_label_by_name(db, name=label_name) # Use get_label_by_name
    if db_label is None:
        raise HTTPException(status_code=404, detail=f"Label '{label_name}' not found")
    return db_label

@app.put("/api/labels/{label_name}", response_model=schemas.Label, tags=["Labels"])
async def update_label_endpoint(label_name: str, label: schemas.LabelCreate, db: Session = Depends(get_db)): # Changed label_id to label_name
    try:
        updated_label = crud.update_label(db=db, name=label_name, label_update=label)
    except ValueError as e: # Catch potential ValueError from CRUD for name conflicts
        raise HTTPException(status_code=400, detail=str(e))

    if updated_label is None:
        # This implies the original label_name was not found by crud.update_label
        raise HTTPException(status_code=404, detail=f"Label '{label_name}' not found to update")
    return updated_label

@app.delete("/api/labels/{label_name}", response_model=schemas.Label, tags=["Labels"])
async def delete_label_endpoint(label_name: str, db: Session = Depends(get_db)): # Changed label_id to label_name
    deleted_label = crud.delete_label(db=db, name=label_name) # Use name
    if deleted_label is None:
        raise HTTPException(status_code=404, detail=f"Label '{label_name}' not found or could not be deleted")
    return deleted_label

# BoardGame Endpoints
@app.post("/api/boardgames/", response_model=schemas.BoardGame, tags=["BoardGames"])
async def create_board_game_endpoint(game: schemas.BoardGameCreate, db: Session = Depends(get_db)):
    return crud.create_board_game(db=db, game=game)

@app.get("/api/boardgames/", response_model=List[schemas.BoardGame], tags=["BoardGames"])
async def get_board_games_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    games = crud.get_board_games(db, skip=skip, limit=limit)
    return games

@app.get("/api/boardgames/{game_name}", response_model=schemas.BoardGame, tags=["BoardGames"])
async def get_board_game_endpoint(game_name: str, db: Session = Depends(get_db)): # Changed game_id to game_name
    db_game = crud.get_board_game_by_name(db, name=game_name) # Use get_board_game_by_name
    if db_game is None:
        raise HTTPException(status_code=404, detail=f"Board game '{game_name}' not found")
    return db_game

@app.put("/api/boardgames/{game_name}", response_model=schemas.BoardGame, tags=["BoardGames"])
async def update_board_game_endpoint(game_name: str, game: schemas.BoardGameUpdate, db: Session = Depends(get_db)): # Changed game_id to game_name
    try:
        updated_game = crud.update_board_game(db=db, name=game_name, game_update=game)
    except ValueError as e: # Catch potential ValueError from CRUD for name conflicts
        raise HTTPException(status_code=400, detail=str(e))

    if updated_game is None:
        # This implies the original game_name was not found by crud.update_board_game
        raise HTTPException(status_code=404, detail=f"Board game '{game_name}' not found to update")
    return updated_game

@app.delete("/api/boardgames/{game_name}", response_model=schemas.BoardGame, tags=["BoardGames"])
async def delete_board_game_endpoint(game_name: str, db: Session = Depends(get_db)): # Changed game_id to game_name
    deleted_game = crud.delete_board_game(db=db, name=game_name) # Use name
    if deleted_game is None:
        raise HTTPException(status_code=404, detail=f"Board game '{game_name}' not found or could not be deleted")
    return deleted_game
