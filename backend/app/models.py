from sqlalchemy import Column, Integer, String, Table, ForeignKey, Identity
from sqlalchemy.orm import relationship
from .database import Base # Using Base from .database

# Association table for Many-to-Many between BoardGame and Label
game_labels = Table(
    'game_labels',
    Base.metadata,
    Column('game_name', String, ForeignKey('boardgames.name'), primary_key=True), # Changed game_id to game_name, FK to boardgames.name
    Column('label_name', String, ForeignKey('labels.name'), primary_key=True) # Changed label_id to label_name and FK to labels.name
)

class BoardGame(Base):
    __tablename__ = "boardgames"

    # id column removed
    name = Column(String, primary_key=True, nullable=False, unique=True, index=True) # Now primary key
    editor_name = Column(String)
    num_players_min = Column(Integer)
    num_players_max = Column(Integer)
    age_min = Column(Integer)
    time_duration_mean = Column(Integer, nullable=True) # Added nullable=True

    labels = relationship(
        "Label",
        secondary=game_labels,
        back_populates="games"
    )

class Label(Base):
    __tablename__ = "labels"

    # id column removed
    name = Column(String, primary_key=True, nullable=False, unique=True) # Now primary key

    games = relationship(
        "BoardGame",
        secondary=game_labels,
        back_populates="labels"
    )
