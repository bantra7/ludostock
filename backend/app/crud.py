from sqlalchemy.orm import Session


from . import models, schemas

def get_games(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Game).offset(skip).limit(limit).all()


def get_game(db: Session, game_id: int):
    return db.query(models.Game).filter(models.Game.game_id == game_id).first()


def create_game(db: Session, game: schemas.Game):
    db_game = models.Game(**game.dict())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game
