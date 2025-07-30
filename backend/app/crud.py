from sqlalchemy.orm import Session
from . import models, schemas

# ============================
# GAME CRUD
# ============================
def get_games(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Game).offset(skip).limit(limit).all()

def get_game(db: Session, game_id: int):
    return db.query(models.Game).filter(models.Game.id == game_id).first()

def create_game(db: Session, game: schemas.GameCreate):
    game_data = game.model_dump()
    author_names = game_data.pop('authors', [])
    artist_names = game_data.pop('artists', [])
    editor_names = game_data.pop('editors', [])
    distributor_names = game_data.pop('distributors', [])

    db_game = models.Game(**game_data)

    # Authors
    for name in author_names:
        db_author = db.query(models.Author).filter(models.Author.name == name).first()
        if not db_author:
            db_author = models.Author(name=name)
            db.add(db_author)
            db.commit()
            db.refresh(db_author)
        db_game.authors.append(db_author)

    # Artists
    for name in artist_names:
        db_artist = db.query(models.Artist).filter(models.Artist.name == name).first()
        if not db_artist:
            db_artist = models.Artist(name=name)
            db.add(db_artist)
            db.commit()
            db.refresh(db_artist)
        db_game.artists.append(db_artist)

    # Editors
    for name in editor_names:
        db_editor = db.query(models.Editor).filter(models.Editor.name == name).first()
        if not db_editor:
            db_editor = models.Editor(name=name)
            db.add(db_editor)
            db.commit()
            db.refresh(db_editor)
        db_game.editors.append(db_editor)

    # Distributors
    for name in distributor_names:
        db_distributor = db.query(models.Distributor).filter(models.Distributor.name == name).first()
        if not db_distributor:
            db_distributor = models.Distributor(name=name)
            db.add(db_distributor)
            db.commit()
            db.refresh(db_distributor)
        db_game.distributors.append(db_distributor)

    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game

def delete_game(db: Session, game_id: int):
    db_game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if db_game:
        db.delete(db_game)
        db.commit()
    return db_game

# ============================
# AUTHOR CRUD
# ============================
def get_authors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Author).offset(skip).limit(limit).all()

def get_author(db: Session, author_id: int):
    return db.query(models.Author).filter(models.Author.id == author_id).first()

def create_author(db: Session, author: schemas.AuthorCreate):
    db_author = models.Author(name=author.name)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

def delete_author(db: Session, author_id: int):
    db_author = db.query(models.Author).filter(models.Author.id == author_id).first()
    if db_author:
        db.delete(db_author)
        db.commit()
    return db_author

# ============================
# ARTIST CRUD
# ============================
def get_artists(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Artist).offset(skip).limit(limit).all()

def get_artist(db: Session, artist_id: int):
    return db.query(models.Artist).filter(models.Artist.id == artist_id).first()

def create_artist(db: Session, artist: schemas.ArtistCreate):
    db_artist = models.Artist(name=artist.name)
    db.add(db_artist)
    db.commit()
    db.refresh(db_artist)
    return db_artist

def delete_artist(db: Session, artist_id: int):
    db_artist = db.query(models.Artist).filter(models.Artist.id == artist_id).first()
    if db_artist:
        db.delete(db_artist)
        db.commit()
    return db_artist

# ============================
# EDITOR CRUD
# ============================
def get_editors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Editor).offset(skip).limit(limit).all()

def get_editor(db: Session, editor_id: int):
    return db.query(models.Editor).filter(models.Editor.id == editor_id).first()

def create_editor(db: Session, editor: schemas.EditorCreate):
    db_editor = models.Editor(name=editor.name)
    db.add(db_editor)
    db.commit()
    db.refresh(db_editor)
    return db_editor

def delete_editor(db: Session, editor_id: int):
    db_editor = db.query(models.Editor).filter(models.Editor.id == editor_id).first()
    if db_editor:
        db.delete(db_editor)
        db.commit()
    return db_editor

# ============================
# DISTRIBUTOR CRUD
# ============================
def get_distributors(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Distributor).offset(skip).limit(limit).all()

def get_distributor(db: Session, distributor_id: int):
    return db.query(models.Distributor).filter(models.Distributor.id == distributor_id).first()

def create_distributor(db: Session, distributor: schemas.DistributorCreate):
    db_distributor = models.Distributor(name=distributor.name)
    db.add(db_distributor)
    db.commit()
    db.refresh(db_distributor)
    return db_distributor

def delete_distributor(db: Session, distributor_id: int):
    db_distributor = db.query(models.Distributor).filter(models.Distributor.id == distributor_id).first()
    if db_distributor:
        db.delete(db_distributor)
        db.commit()
    return db_distributor

# ============================
# USER CRUD
# ============================
def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user(db: Session, user_id):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email, username=user.username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

# ============================
# COLLECTION CRUD
# ============================
def get_collections(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Collection).offset(skip).limit(limit).all()

def get_collection(db: Session, collection_id: int):
    return db.query(models.Collection).filter(models.Collection.id == collection_id).first()

def create_collection(db: Session, collection: schemas.CollectionCreate, owner_id):
    db_collection = models.Collection(
        name=collection.name,
        description=collection.description,
        owner_id=owner_id
    )
    db.add(db_collection)
    db.commit()
    db.refresh(db_collection)
    return db_collection

def delete_collection(db: Session, collection_id: int):
    db_collection = db.query(models.Collection).filter(models.Collection.id == collection_id).first()
    if db_collection:
        db.delete(db_collection)
        db.commit()
    return db_collection

# ============================
# COLLECTION SHARE CRUD
# ============================
def get_collection_shares(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CollectionShare).offset(skip).limit(limit).all()

def get_collection_share(db: Session, share_id: int):
    return db.query(models.CollectionShare).filter(models.CollectionShare.id == share_id).first()

def create_collection_share(db: Session, share: schemas.CollectionShareCreate, collection_id: int):
    db_share = models.CollectionShare(
        collection_id=collection_id,
        shared_with=share.shared_with,
        permission=share.permission
    )
    db.add(db_share)
    db.commit()
    db.refresh(db_share)
    return db_share

def delete_collection_share(db: Session, share_id: int):
    db_share = db.query(models.CollectionShare).filter(models.CollectionShare.id == share_id).first()
    if db_share:
        db.delete(db_share)
        db.commit()
    return db_share

# ============================
# USER LOCATION CRUD
# ============================
def get_user_locations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.UserLocation).offset(skip).limit(limit).all()

def get_user_location(db: Session, location_id: int):
    return db.query(models.UserLocation).filter(models.UserLocation.id == location_id).first()

def create_user_location(db: Session, location: schemas.UserLocationCreate, user_id):
    db_location = models.UserLocation(
        name=location.name,
        user_id=user_id
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def delete_user_location(db: Session, location_id: int):
    db_location = db.query(models.UserLocation).filter(models.UserLocation.id == location_id).first()
    if db_location:
        db.delete(db_location)
        db.commit()
    return db_location

# ============================
# COLLECTION GAME CRUD
# ============================
def get_collection_games(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CollectionGame).offset(skip).limit(limit).all()

def get_collection_game(db: Session, collection_game_id: int):
    return db.query(models.CollectionGame).filter(models.CollectionGame.id == collection_game_id).first()

def create_collection_game(db: Session, collection_game: schemas.CollectionGameCreate):
    db_collection_game = models.CollectionGame(
        collection_id=collection_game.collection_id,
        game_id=collection_game.game_id,
        location_id=collection_game.location_id,
        quantity=collection_game.quantity
    )
    db.add(db_collection_game)
    db.commit()
    db.refresh(db_collection_game)
    return db_collection_game

def delete_collection_game(db: Session, collection_game_id: int):
    db_collection_game = db.query(models.CollectionGame).filter(models.CollectionGame.id == collection_game_id).first()
    if db_collection_game:
        db.delete(db_collection_game)
        db.commit()
    return db_collection_game