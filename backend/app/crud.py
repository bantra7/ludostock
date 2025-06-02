from sqlalchemy.orm import Session
from . import models, schemas

# BoardGame CRUD functions
def get_board_games(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BoardGame).offset(skip).limit(limit).all()

def get_board_game(db: Session, game_id: int):
    return db.query(models.BoardGame).filter(models.BoardGame.id == game_id).first()

def create_board_game(db: Session, game: schemas.BoardGameCreate):
    game_data = game.dict() # Get all data from the input schema
    label_names = game_data.pop('labels', []) # Pop labels, default to empty list if not provided

    # Create BoardGame instance with remaining scalar fields from game_data
    # This assumes BoardGameCreate has fields corresponding to BoardGame model's scalar attributes
    db_game = models.BoardGame(**game_data)

    # Process labels
    for label_name in label_names:
        db_label = get_label_by_name(db, name=label_name) # Assumes get_label_by_name is defined
        if db_label is None:
            # Assumes create_label is defined and handles commit for the new label
            db_label = create_label(db, schemas.LabelCreate(name=label_name))
        db_game.labels.append(db_label)

    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game

def update_board_game(db: Session, game_id: int, game_update: schemas.BoardGameCreate):
    db_game = db.query(models.BoardGame).filter(models.BoardGame.id == game_id).first()
    if db_game:
        # Get all fields from the update schema. `exclude_unset=True` means only provided fields are included.
        update_data = game_update.dict(exclude_unset=True)

        # Pop 'labels' for separate handling. If 'labels' is not in update_data, label_names will be None.
        label_names = update_data.pop('labels', None)

        # Update scalar fields on the db_game model
        for key, value in update_data.items():
            setattr(db_game, key, value)

        # Update labels only if 'labels' key was present in game_update payload
        if label_names is not None: # This means 'labels' was part of the request
            new_labels = []
            for label_name in label_names: # label_names could be an empty list
                db_label = get_label_by_name(db, name=label_name)
                if db_label is None:
                    db_label = create_label(db, schemas.LabelCreate(name=label_name))
                new_labels.append(db_label)
            db_game.labels = new_labels # Assign the new list of label objects

        db.commit()
        db.refresh(db_game)
    return db_game

def delete_board_game(db: Session, game_id: int):
    db_game = db.query(models.BoardGame).filter(models.BoardGame.id == game_id).first()
    if db_game:
        db.delete(db_game)
        db.commit()
    return db_game

# Label CRUD functions (from previous step)
def get_label(db: Session, label_id: int):
    return db.query(models.Label).filter(models.Label.id == label_id).first()

def get_label_by_name(db: Session, name: str):
    return db.query(models.Label).filter(models.Label.name == name).first()

def get_labels(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Label).offset(skip).limit(limit).all()

def create_label(db: Session, label: schemas.LabelCreate):
    db_label = models.Label(name=label.name)
    db.add(db_label)
    db.commit()
    db.refresh(db_label)
    return db_label

def update_label(db: Session, label_id: int, label_update: schemas.LabelCreate):
    db_label = db.query(models.Label).filter(models.Label.id == label_id).first()
    if db_label:
        db_label.name = label_update.name
        db.commit()
        db.refresh(db_label)
    return db_label

def delete_label(db: Session, label_id: int):
    db_label = db.query(models.Label).filter(models.Label.id == label_id).first()
    if db_label:
        db.delete(db_label)
        db.commit()
    return db_label # Returns the deleted object or None
