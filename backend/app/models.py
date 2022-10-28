from sqlalchemy.ext.declarative import declarative_base
from .database import Base
from sqlalchemy import Column, String, Integer

Base = declarative_base()


class Game(Base):
    __tablename__ = "games"

    game_id = Column(Integer, primary_key=True)
    title = Column(String, unique=False, index=True)
    # nb_players_max
    # nb_players_min
    # age_max
    # age_min
    # duration_max
    # duration_min
    # labels
    # difficulty
    # authors
    # editors
    # illustrators


class Label(Base):
    __tablename__ = "labels"

    label_id = Column(Integer, primary_key=True)
    value = Column(String, unique=True, index=True)
    color = Column(String, unique=False, index=True)
