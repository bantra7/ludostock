from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from environs import Env
from sqlalchemy.orm import Session
from . import crud, schemas
from .database import SessionLocal, init_db

env = Env()
env.read_env(env.str('ENV_PATH', '.env'))

db_path = env.str("DATABASE_URL").replace("duckdb:///", "")
sql_file = env.str("SQL_CREATION_FILE")

if not os.path.exists(db_path):
    print("Initialisation DB...")
    init_db(sql_file)
    print("DB initialisée.")
else:
    print("DB déjà existante.")
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================
# GAME ENDPOINTS
# ============================
@app.post("/api/games/", response_model=schemas.Game, tags=["Games"])
def create_game(game: schemas.GameCreate, db: Session = Depends(get_db)):
    return crud.create_game(db=db, game=game)

@app.get("/api/games/", response_model=List[schemas.Game], tags=["Games"])
def get_games(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_games(db, skip=skip, limit=limit)

@app.get("/api/games/{game_id}", response_model=schemas.Game, tags=["Games"])
def get_game(game_id: int, db: Session = Depends(get_db)):
    db_game = crud.get_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return db_game

@app.delete("/api/games/{game_id}", response_model=schemas.Game, tags=["Games"])
def delete_game(game_id: int, db: Session = Depends(get_db)):
    db_game = crud.delete_game(db, game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return db_game

# ============================
# AUTHOR ENDPOINTS
# ============================
@app.post("/api/authors/", response_model=schemas.Author, tags=["Authors"])
def create_author(author: schemas.AuthorCreate, db: Session = Depends(get_db)):
    return crud.create_author(db=db, author=author)

@app.get("/api/authors/", response_model=List[schemas.Author], tags=["Authors"])
def get_authors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_authors(db, skip=skip, limit=limit)

@app.get("/api/authors/{author_id}", response_model=schemas.Author, tags=["Authors"])
def get_author(author_id: int, db: Session = Depends(get_db)):
    db_author = crud.get_author(db, author_id=author_id)
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return db_author

@app.delete("/api/authors/{author_id}", response_model=schemas.Author, tags=["Authors"])
def delete_author(author_id: int, db: Session = Depends(get_db)):
    db_author = crud.delete_author(db, author_id=author_id)
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return db_author

# ============================
# ARTIST ENDPOINTS
# ============================
@app.post("/api/artists/", response_model=schemas.Artist, tags=["Artists"])
def create_artist(artist: schemas.ArtistCreate, db: Session = Depends(get_db)):
    return crud.create_artist(db=db, artist=artist)

@app.get("/api/artists/", response_model=List[schemas.Artist], tags=["Artists"])
def get_artists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_artists(db, skip=skip, limit=limit)

@app.get("/api/artists/{artist_id}", response_model=schemas.Artist, tags=["Artists"])
def get_artist(artist_id: int, db: Session = Depends(get_db)):
    db_artist = crud.get_artist(db, artist_id=artist_id)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return db_artist

@app.delete("/api/artists/{artist_id}", response_model=schemas.Artist, tags=["Artists"])
def delete_artist(artist_id: int, db: Session = Depends(get_db)):
    db_artist = crud.delete_artist(db, artist_id=artist_id)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return db_artist

# ============================
# EDITOR ENDPOINTS
# ============================
@app.post("/api/editors/", response_model=schemas.Editor, tags=["Editors"])
def create_editor(editor: schemas.EditorCreate, db: Session = Depends(get_db)):
    return crud.create_editor(db=db, editor=editor)

@app.get("/api/editors/", response_model=List[schemas.Editor], tags=["Editors"])
def get_editors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_editors(db, skip=skip, limit=limit)

@app.get("/api/editors/{editor_id}", response_model=schemas.Editor, tags=["Editors"])
def get_editor(editor_id: int, db: Session = Depends(get_db)):
    db_editor = crud.get_editor(db, editor_id=editor_id)
    if db_editor is None:
        raise HTTPException(status_code=404, detail="Editor not found")
    return db_editor

@app.delete("/api/editors/{editor_id}", response_model=schemas.Editor, tags=["Editors"])
def delete_editor(editor_id: int, db: Session = Depends(get_db)):
    db_editor = crud.delete_editor(db, editor_id=editor_id)
    if db_editor is None:
        raise HTTPException(status_code=404, detail="Editor not found")
    return db_editor

# ============================
# DISTRIBUTOR ENDPOINTS
# ============================
@app.post("/api/distributors/", response_model=schemas.Distributor, tags=["Distributors"])
def create_distributor(distributor: schemas.DistributorCreate, db: Session = Depends(get_db)):
    return crud.create_distributor(db=db, distributor=distributor)

@app.get("/api/distributors/", response_model=List[schemas.Distributor], tags=["Distributors"])
def get_distributors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_distributors(db, skip=skip, limit=limit)

@app.get("/api/distributors/{distributor_id}", response_model=schemas.Distributor, tags=["Distributors"])
def get_distributor(distributor_id: int, db: Session = Depends(get_db)):
    db_distributor = crud.get_distributor(db, distributor_id=distributor_id)
    if db_distributor is None:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return db_distributor

@app.delete("/api/distributors/{distributor_id}", response_model=schemas.Distributor, tags=["Distributors"])
def delete_distributor(distributor_id: int, db: Session = Depends(get_db)):
    db_distributor = crud.delete_distributor(db, distributor_id=distributor_id)
    if db_distributor is None:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return db_distributor

# ============================
# USER ENDPOINTS
# ============================
@app.post("/api/users/", response_model=schemas.User, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)

@app.get("/api/users/", response_model=List[schemas.User], tags=["Users"])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)

@app.get("/api/users/{user_id}", response_model=schemas.User, tags=["Users"])
def get_user(user_id: str, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/api/users/{user_id}", response_model=schemas.User, tags=["Users"])
def delete_user(user_id: str, db: Session = Depends(get_db)):
    db_user = crud.delete_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# ============================
# COLLECTION ENDPOINTS
# ============================
@app.post("/api/collections/", response_model=schemas.Collection, tags=["Collections"])
def create_collection(collection: schemas.CollectionCreate, owner_id: str, db: Session = Depends(get_db)):
    return crud.create_collection(db=db, collection=collection, owner_id=owner_id)

@app.get("/api/collections/", response_model=List[schemas.Collection], tags=["Collections"])
def get_collections(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_collections(db, skip=skip, limit=limit)

@app.get("/api/collections/{collection_id}", response_model=schemas.Collection, tags=["Collections"])
def get_collection(collection_id: int, db: Session = Depends(get_db)):
    db_collection = crud.get_collection(db, collection_id=collection_id)
    if db_collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return db_collection

@app.delete("/api/collections/{collection_id}", response_model=schemas.Collection, tags=["Collections"])
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    db_collection = crud.delete_collection(db, collection_id=collection_id)
    if db_collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return db_collection

# ============================
# COLLECTION SHARE ENDPOINTS
# ============================
@app.post("/api/collection_shares/", response_model=schemas.CollectionShare, tags=["CollectionShares"])
def create_collection_share(share: schemas.CollectionShareCreate, collection_id: int, db: Session = Depends(get_db)):
    return crud.create_collection_share(db=db, share=share, collection_id=collection_id)

@app.get("/api/collection_shares/", response_model=List[schemas.CollectionShare], tags=["CollectionShares"])
def get_collection_shares(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_collection_shares(db, skip=skip, limit=limit)

@app.get("/api/collection_shares/{share_id}", response_model=schemas.CollectionShare, tags=["CollectionShares"])
def get_collection_share(share_id: int, db: Session = Depends(get_db)):
    db_share = crud.get_collection_share(db, share_id=share_id)
    if db_share is None:
        raise HTTPException(status_code=404, detail="Collection share not found")
    return db_share

@app.delete("/api/collection_shares/{share_id}", response_model=schemas.CollectionShare, tags=["CollectionShares"])
def delete_collection_share(share_id: int, db: Session = Depends(get_db)):
    db_share = crud.delete_collection_share(db, share_id=share_id)
    if db_share is None:
        raise HTTPException(status_code=404, detail="Collection share not found")
    return db_share

# ============================
# USER LOCATION ENDPOINTS
# ============================
@app.post("/api/user_locations/", response_model=schemas.UserLocation, tags=["UserLocations"])
def create_user_location(location: schemas.UserLocationCreate, user_id: str, db: Session = Depends(get_db)):
    return crud.create_user_location(db=db, location=location, user_id=user_id)

@app.get("/api/user_locations/", response_model=List[schemas.UserLocation], tags=["UserLocations"])
def get_user_locations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_user_locations(db, skip=skip, limit=limit)

@app.get("/api/user_locations/{location_id}", response_model=schemas.UserLocation, tags=["UserLocations"])
def get_user_location(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.get_user_location(db, location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="User location not found")
    return db_location

@app.delete("/api/user_locations/{location_id}", response_model=schemas.UserLocation, tags=["UserLocations"])
def delete_user_location(location_id: int, db: Session = Depends(get_db)):
    db_location = crud.delete_user_location(db, location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="User location not found")
    return db_location

# ============================
# COLLECTION GAME ENDPOINTS
# ============================
@app.post("/api/collection_games/", response_model=schemas.CollectionGame, tags=["CollectionGames"])
def create_collection_game(collection_game: schemas.CollectionGameCreate, db: Session = Depends(get_db)):
    return crud.create_collection_game(db=db, collection_game=collection_game)

@app.get("/api/collection_games/", response_model=List[schemas.CollectionGame], tags=["CollectionGames"])
def get_collection_games(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_collection_games(db, skip=skip, limit=limit)

@app.get("/api/collection_games/{collection_game_id}", response_model=schemas.CollectionGame, tags=["CollectionGames"])
def get_collection_game(collection_game_id: int, db: Session = Depends(get_db)):
    db_collection_game = crud.get_collection_game(db, collection_game_id=collection_game_id)
    if db_collection_game is None:
        raise HTTPException(status_code=404, detail="Collection game not found")
    return db_collection_game

@app.delete("/api/collection_games/{collection_game_id}", response_model=schemas.CollectionGame, tags=["CollectionGames"])
def delete_collection_game(collection_game_id: int, db: Session = Depends(get_db)):
    db_collection_game = crud.delete_collection_game(db, collection_game_id=collection_game_id)
    if db_collection_game is None:
        raise HTTPException(status_code=404, detail="Collection game not found")
    return db_collection_game