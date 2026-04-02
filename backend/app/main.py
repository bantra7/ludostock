"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import crud, schemas
from .config import ALLOW_ORIGINS
from .database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize the SQLite database on startup."""
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/games/", response_model=schemas.Game, tags=["Games"])
def create_game(game: schemas.GameCreate):
    """Create a game."""
    return crud.create_game(game=game)


@app.get("/api/games/", response_model=List[schemas.Game], tags=["Games"])
def get_games(skip: int = 0, limit: int = 100):
    """List games."""
    return crud.get_games(skip=skip, limit=limit)


@app.get("/api/games/{game_id}", response_model=schemas.Game, tags=["Games"])
def get_game(game_id: int):
    """Get a game by id."""
    db_game = crud.get_game(game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return db_game


@app.delete("/api/games/{game_id}", response_model=schemas.Game, tags=["Games"])
def delete_game(game_id: int):
    """Delete a game."""
    db_game = crud.delete_game(game_id=game_id)
    if db_game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return db_game


@app.post("/api/authors/", response_model=schemas.Author, tags=["Authors"])
def create_author(author: schemas.AuthorCreate):
    """Create an author."""
    return crud.create_author(author=author)


@app.get("/api/authors/", response_model=List[schemas.Author], tags=["Authors"])
def get_authors(skip: int = 0, limit: int = 100):
    """List authors."""
    return crud.get_authors(skip=skip, limit=limit)


@app.get("/api/authors/{author_id}", response_model=schemas.Author, tags=["Authors"])
def get_author(author_id: int):
    """Get an author by id."""
    db_author = crud.get_author(author_id=author_id)
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return db_author


@app.delete("/api/authors/{author_id}", response_model=schemas.Author, tags=["Authors"])
def delete_author(author_id: int):
    """Delete an author."""
    db_author = crud.delete_author(author_id=author_id)
    if db_author is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return db_author


@app.post("/api/artists/", response_model=schemas.Artist, tags=["Artists"])
def create_artist(artist: schemas.ArtistCreate):
    """Create an artist."""
    return crud.create_artist(artist=artist)


@app.get("/api/artists/", response_model=List[schemas.Artist], tags=["Artists"])
def get_artists(skip: int = 0, limit: int = 100):
    """List artists."""
    return crud.get_artists(skip=skip, limit=limit)


@app.get("/api/artists/{artist_id}", response_model=schemas.Artist, tags=["Artists"])
def get_artist(artist_id: int):
    """Get an artist by id."""
    db_artist = crud.get_artist(artist_id=artist_id)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return db_artist


@app.delete("/api/artists/{artist_id}", response_model=schemas.Artist, tags=["Artists"])
def delete_artist(artist_id: int):
    """Delete an artist."""
    db_artist = crud.delete_artist(artist_id=artist_id)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return db_artist


@app.post("/api/editors/", response_model=schemas.Editor, tags=["Editors"])
def create_editor(editor: schemas.EditorCreate):
    """Create an editor."""
    return crud.create_editor(editor=editor)


@app.get("/api/editors/", response_model=List[schemas.Editor], tags=["Editors"])
def get_editors(skip: int = 0, limit: int = 100):
    """List editors."""
    return crud.get_editors(skip=skip, limit=limit)


@app.get("/api/editors/{editor_id}", response_model=schemas.Editor, tags=["Editors"])
def get_editor(editor_id: int):
    """Get an editor by id."""
    db_editor = crud.get_editor(editor_id=editor_id)
    if db_editor is None:
        raise HTTPException(status_code=404, detail="Editor not found")
    return db_editor


@app.delete("/api/editors/{editor_id}", response_model=schemas.Editor, tags=["Editors"])
def delete_editor(editor_id: int):
    """Delete an editor."""
    db_editor = crud.delete_editor(editor_id=editor_id)
    if db_editor is None:
        raise HTTPException(status_code=404, detail="Editor not found")
    return db_editor


@app.post("/api/distributors/", response_model=schemas.Distributor, tags=["Distributors"])
def create_distributor(distributor: schemas.DistributorCreate):
    """Create a distributor."""
    return crud.create_distributor(distributor=distributor)


@app.get("/api/distributors/", response_model=List[schemas.Distributor], tags=["Distributors"])
def get_distributors(skip: int = 0, limit: int = 100):
    """List distributors."""
    return crud.get_distributors(skip=skip, limit=limit)


@app.get("/api/distributors/{distributor_id}", response_model=schemas.Distributor, tags=["Distributors"])
def get_distributor(distributor_id: int):
    """Get a distributor by id."""
    db_distributor = crud.get_distributor(distributor_id=distributor_id)
    if db_distributor is None:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return db_distributor


@app.delete("/api/distributors/{distributor_id}", response_model=schemas.Distributor, tags=["Distributors"])
def delete_distributor(distributor_id: int):
    """Delete a distributor."""
    db_distributor = crud.delete_distributor(distributor_id=distributor_id)
    if db_distributor is None:
        raise HTTPException(status_code=404, detail="Distributor not found")
    return db_distributor


@app.post("/api/users/", response_model=schemas.User, tags=["Users"])
def create_user(user: schemas.UserCreate):
    """Create a user."""
    return crud.create_user(user=user)


@app.get("/api/users/", response_model=List[schemas.User], tags=["Users"])
def get_users(skip: int = 0, limit: int = 100):
    """List users."""
    return crud.get_users(skip=skip, limit=limit)


@app.get("/api/users/{user_id}", response_model=schemas.User, tags=["Users"])
def get_user(user_id: str):
    """Get a user by id."""
    db_user = crud.get_user(user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/api/users/{user_id}", response_model=schemas.User, tags=["Users"])
def delete_user(user_id: str):
    """Delete a user."""
    db_user = crud.delete_user(user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/api/collections/", response_model=schemas.Collection, tags=["Collections"])
def create_collection(collection: schemas.CollectionCreate):
    """Create a collection."""
    return crud.create_collection(collection=collection)


@app.get("/api/collections/", response_model=List[schemas.Collection], tags=["Collections"])
def get_collections(skip: int = 0, limit: int = 100):
    """List collections."""
    return crud.get_collections(skip=skip, limit=limit)


@app.get("/api/collections/{collection_id}", response_model=schemas.Collection, tags=["Collections"])
def get_collection(collection_id: int):
    """Get a collection by id."""
    db_collection = crud.get_collection(collection_id=collection_id)
    if db_collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return db_collection


@app.delete("/api/collections/{collection_id}", response_model=schemas.Collection, tags=["Collections"])
def delete_collection(collection_id: int):
    """Delete a collection."""
    db_collection = crud.delete_collection(collection_id=collection_id)
    if db_collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return db_collection


@app.post("/api/collection_shares/", response_model=schemas.CollectionShare, tags=["CollectionShares"])
def create_collection_share(share: schemas.CollectionShareCreate, collection_id: int):
    """Create a collection share."""
    db_collection = crud.get_collection(collection_id=collection_id)
    if db_collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")
    return crud.create_collection_share(share=share, collection_id=collection_id)


@app.get("/api/collection_shares/", response_model=List[schemas.CollectionShare], tags=["CollectionShares"])
def get_collection_shares(skip: int = 0, limit: int = 100):
    """List collection shares."""
    return crud.get_collection_shares(skip=skip, limit=limit)


@app.get("/api/collection_shares/{share_id}", response_model=schemas.CollectionShare, tags=["CollectionShares"])
def get_collection_share(share_id: int):
    """Get a collection share by id."""
    db_share = crud.get_collection_share(share_id=share_id)
    if db_share is None:
        raise HTTPException(status_code=404, detail="Collection share not found")
    return db_share


@app.delete("/api/collection_shares/{share_id}", response_model=schemas.CollectionShare, tags=["CollectionShares"])
def delete_collection_share(share_id: int):
    """Delete a collection share."""
    db_share = crud.delete_collection_share(share_id=share_id)
    if db_share is None:
        raise HTTPException(status_code=404, detail="Collection share not found")
    return db_share


@app.post("/api/user_locations/", response_model=schemas.UserLocation, tags=["UserLocations"])
def create_user_location(location: schemas.UserLocationCreate):
    """Create a user location."""
    return crud.create_user_location(location=location)


@app.get("/api/user_locations/", response_model=List[schemas.UserLocation], tags=["UserLocations"])
def get_user_locations(skip: int = 0, limit: int = 100):
    """List user locations."""
    return crud.get_user_locations(skip=skip, limit=limit)


@app.get("/api/user_locations/{location_id}", response_model=schemas.UserLocation, tags=["UserLocations"])
def get_user_location(location_id: int):
    """Get a user location by id."""
    db_location = crud.get_user_location(location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="User location not found")
    return db_location


@app.delete("/api/user_locations/{location_id}", response_model=schemas.UserLocation, tags=["UserLocations"])
def delete_user_location(location_id: int):
    """Delete a user location."""
    db_location = crud.delete_user_location(location_id=location_id)
    if db_location is None:
        raise HTTPException(status_code=404, detail="User location not found")
    return db_location


@app.post("/api/collection_games/", response_model=schemas.CollectionGame, tags=["CollectionGames"])
def create_collection_game(collection_game: schemas.CollectionGameCreate):
    """Create a collection game."""
    return crud.create_collection_game(collection_game=collection_game)


@app.get("/api/collection_games/", response_model=List[schemas.CollectionGame], tags=["CollectionGames"])
def get_collection_games(skip: int = 0, limit: int = 100):
    """List collection games."""
    return crud.get_collection_games(skip=skip, limit=limit)


@app.get("/api/collection_games/{collection_game_id}", response_model=schemas.CollectionGame, tags=["CollectionGames"])
def get_collection_game(collection_game_id: int):
    """Get a collection game by id."""
    db_collection_game = crud.get_collection_game(collection_game_id=collection_game_id)
    if db_collection_game is None:
        raise HTTPException(status_code=404, detail="Collection game not found")
    return db_collection_game


@app.delete("/api/collection_games/{collection_game_id}", response_model=schemas.CollectionGame, tags=["CollectionGames"])
def delete_collection_game(collection_game_id: int):
    """Delete a collection game."""
    db_collection_game = crud.delete_collection_game(collection_game_id=collection_game_id)
    if db_collection_game is None:
        raise HTTPException(status_code=404, detail="Collection game not found")
    return db_collection_game
