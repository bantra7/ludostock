from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, UniqueConstraint, CheckConstraint, Sequence
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base

# ============================
# Séquences pour auto-incrément
games_seq = Sequence('games_seq')
authors_seq = Sequence('authors_seq')
artists_seq = Sequence('artists_seq')
editors_seq = Sequence('editors_seq')
distributors_seq = Sequence('distributors_seq')
users_seq = Sequence('users_seq')
collections_seq = Sequence('collections_seq')
collection_shares_seq = Sequence('collection_shares_seq')
user_locations_seq = Sequence('user_locations_seq')
collection_games_seq = Sequence('collection_games_seq')

# ============================
# TABLE PRINCIPALE : GAMES
# ============================
class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, games_seq, primary_key=True)
    name = Column(Text, nullable=False)
    type = Column(Text, nullable=False)
    extension_of_id = Column(Integer, ForeignKey("games.id"), nullable=True)
    creation_year = Column(Integer)
    min_players = Column(Integer)
    max_players = Column(Integer)
    min_age = Column(Integer)
    duration_minutes = Column(Integer)
    url = Column(Text)
    image_url = Column(Text)

    authors = relationship("Author", secondary="game_authors", back_populates="games")
    artists = relationship("Artist", secondary="game_artists", back_populates="games")
    editors = relationship("Editor", secondary="game_editors", back_populates="games")
    distributors = relationship("Distributor", secondary="game_distributors", back_populates="games")

# ============================
# TABLES LIÉES
# ============================
class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, authors_seq, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    games = relationship("Game", secondary="game_authors", back_populates="authors")

class Artist(Base):
    __tablename__ = "artists"
    id = Column(Integer, artists_seq, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    games = relationship("Game", secondary="game_artists", back_populates="artists")

class Editor(Base):
    __tablename__ = "editors"
    id = Column(Integer, editors_seq, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    games = relationship("Game", secondary="game_editors", back_populates="editors")

class Distributor(Base):
    __tablename__ = "distributors"
    id = Column(Integer, distributors_seq, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    games = relationship("Game", secondary="game_distributors", back_populates="distributors")

# ============================
# RELATIONS N-N
# ============================
game_authors = Table(
    "game_authors",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True)
)

game_artists = Table(
    "game_artists",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id"), primary_key=True),
    Column("artist_id", Integer, ForeignKey("artists.id"), primary_key=True)
)

game_editors = Table(
    "game_editors",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id"), primary_key=True),
    Column("editor_id", Integer, ForeignKey("editors.id"), primary_key=True)
)

game_distributors = Table(
    "game_distributors",
    Base.metadata,
    Column("game_id", Integer, ForeignKey("games.id"), primary_key=True),
    Column("distributor_id", Integer, ForeignKey("distributors.id"), primary_key=True)
)

# ============================
# UTILISATEURS
# ============================
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(Text, unique=True, nullable=False)
    username = Column(Text)

    collections = relationship("Collection", back_populates="owner")
    locations = relationship("UserLocation", back_populates="user")

# ============================
# COLLECTIONS DES UTILISATEURS
# ============================
class Collection(Base):
    __tablename__ = "collections"
    id = Column(Integer, collections_seq, primary_key=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(Text, nullable=False)
    description = Column(Text)

    owner = relationship("User", back_populates="collections")
    games = relationship("CollectionGame", back_populates="collection")
    shares = relationship("CollectionShare", back_populates="collection")

# ============================
# PARTAGE DE COLLECTIONS
# ============================
class CollectionShare(Base):
    __tablename__ = "collection_shares"
    id = Column(Integer, collection_shares_seq, primary_key=True)
    collection_id = Column(Integer, ForeignKey("collections.id"))
    shared_with = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    permission = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("collection_id", "shared_with"),
        CheckConstraint("permission IN ('read', 'write')"),
    )

    collection = relationship("Collection", back_populates="shares")

# ============================
# LIEUX (propres à chaque utilisateur)
# ============================
class UserLocation(Base):
    __tablename__ = "user_locations"
    id = Column(Integer, user_locations_seq, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    name = Column(Text, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "name"),)

    user = relationship("User", back_populates="locations")
    games = relationship("CollectionGame", back_populates="location")

# ============================
# JEUX DANS UNE COLLECTION
# ============================
class CollectionGame(Base):
    __tablename__ = "collection_games"
    id = Column(Integer, collection_games_seq, primary_key=True)
    collection_id = Column(Integer, ForeignKey("collections.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    location_id = Column(Integer, ForeignKey("user_locations.id"), nullable=True)
    quantity = Column(Integer, default=1)

    __table_args__ = (UniqueConstraint("collection_id", "game_id", "location_id"),)

    collection = relationship("Collection", back_populates="games")
    location = relationship("UserLocation", back_populates="games")