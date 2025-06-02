import os
from fastapi import Depends, FastAPI, HTTPException # Added HTTPException
from typing import List
from sqlalchemy.orm import Session
from . import crud, models, schemas # models.Base will be accessed via this
from .database import SessionLocal, engine # engine is here

# This line ensures that all tables are created based on models.
# It should be called after all models are defined (which happens when `models` is imported)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Label Endpoints
@app.post("/labels/", response_model=schemas.Label, tags=["Labels"])
async def create_label_endpoint(label: schemas.LabelCreate, db: Session = Depends(get_db)):
    db_label = crud.get_label_by_name(db, name=label.name)
    if db_label:
        raise HTTPException(status_code=400, detail="Label with this name already exists")
    return crud.create_label(db=db, label=label)

@app.get("/labels/", response_model=List[schemas.Label], tags=["Labels"])
async def get_labels_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    labels = crud.get_labels(db, skip=skip, limit=limit)
    return labels

@app.get("/labels/{label_id}", response_model=schemas.Label, tags=["Labels"])
async def get_label_endpoint(label_id: int, db: Session = Depends(get_db)):
    db_label = crud.get_label(db, label_id=label_id)
    if db_label is None:
        raise HTTPException(status_code=404, detail="Label not found")
    return db_label

@app.put("/labels/{label_id}", response_model=schemas.Label, tags=["Labels"])
async def update_label_endpoint(label_id: int, label: schemas.LabelCreate, db: Session = Depends(get_db)):
    # First, check if the label to update exists
    db_label_check = crud.get_label(db, label_id=label_id)
    if db_label_check is None:
        raise HTTPException(status_code=404, detail="Label not found to update")

    # Optional: Check if the new name would conflict with another existing label
    # This depends on business logic (e.g., are names unique, can we rename to an existing name if it's a different ID)
    # For simplicity, crud.update_label might handle this if name has a unique constraint,
    # or it might update. If Label.name is unique, database will raise error.
    # Here, we are primarily updating the found label.

    updated_label = crud.update_label(db=db, label_id=label_id, label_update=label)
    # crud.update_label returns the updated label or None if not found (though we checked)
    if updated_label is None:
        # This case should ideally not be reached if the initial check passed and crud.update_label is robust
        raise HTTPException(status_code=404, detail="Label disappeared during update")
    return updated_label

@app.delete("/labels/{label_id}", response_model=schemas.Label, tags=["Labels"])
async def delete_label_endpoint(label_id: int, db: Session = Depends(get_db)):
    db_label = crud.get_label(db, label_id=label_id) # Check existence for 404
    if db_label is None:
        raise HTTPException(status_code=404, detail="Label not found to delete")

    deleted_label = crud.delete_label(db=db, label_id=label_id)
    # crud.delete_label returns the deleted object or None
    if deleted_label is None:
         # This case should ideally not be reached if the initial check passed.
        raise HTTPException(status_code=404, detail="Label could not be deleted or was already gone.")
    return deleted_label

# BoardGame Endpoints
@app.post("/boardgames/", response_model=schemas.BoardGame, tags=["BoardGames"])
async def create_board_game_endpoint(game: schemas.BoardGameCreate, db: Session = Depends(get_db)):
    return crud.create_board_game(db=db, game=game)

@app.get("/boardgames/", response_model=List[schemas.BoardGame], tags=["BoardGames"])
async def get_board_games_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    games = crud.get_board_games(db, skip=skip, limit=limit)
    return games

@app.get("/boardgames/{game_id}", response_model=schemas.BoardGame, tags=["BoardGames"])
async def get_board_game_endpoint(game_id: int, db: Session = Depends(get_db)):
    db_game = crud.get_board_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Board game not found")
    return db_game

@app.put("/boardgames/{game_id}", response_model=schemas.BoardGame, tags=["BoardGames"])
async def update_board_game_endpoint(game_id: int, game: schemas.BoardGameCreate, db: Session = Depends(get_db)):
    db_game_check = crud.get_board_game(db, game_id=game_id) # Check for existence
    if db_game_check is None:
        raise HTTPException(status_code=404, detail="Board game not found to update")

    updated_game = crud.update_board_game(db=db, game_id=game_id, game_update=game)
    if updated_game is None:
        # Should not happen if check passed and crud is robust
        raise HTTPException(status_code=404, detail="Board game disappeared during update")
    return updated_game

@app.delete("/boardgames/{game_id}", response_model=schemas.BoardGame, tags=["BoardGames"])
async def delete_board_game_endpoint(game_id: int, db: Session = Depends(get_db)):
    db_game_check = crud.get_board_game(db, game_id=game_id) # Check for existence
    if db_game_check is None:
        raise HTTPException(status_code=404, detail="Board game not found to delete")

    deleted_game = crud.delete_board_game(db=db, game_id=game_id)
    if deleted_game is None:
        # Should not happen if check passed
        raise HTTPException(status_code=404, detail="Board game could not be deleted or was already gone.")
    return deleted_game
