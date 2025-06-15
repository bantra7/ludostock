from sqlalchemy import Column, Integer, String, Table, ForeignKey, Identity
from sqlalchemy.orm import relationship
from .database import Base # Using Base from .database

# Association table for Many-to-Many between BoardGame and Label
game_labels = Table(
    'game_labels',
    Base.metadata,
    Column('game_id', Integer, ForeignKey('boardgames.id'), primary_key=True),
    Column('label_id', Integer, ForeignKey('labels.id'), primary_key=True)
)

class BoardGame(Base):
    __tablename__ = "boardgames"

    id = Column(Integer, primary_key=True, index=True) # Renamed from game_id, added index
    name = Column(String, index=True) # Renamed from title
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

    id = Column(Integer, primary_key=True, index=True) # Renamed from label_id, added index
    name = Column(String, unique=True, index=True) # Renamed from value

    games = relationship(
        "BoardGame",
        secondary=game_labels,
        back_populates="labels"
    )
