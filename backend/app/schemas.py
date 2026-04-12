"""Pydantic schemas exposed by the FastAPI API."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrmSchema(BaseModel):
    """Base schema compatible with dicts and attribute-based objects."""

    model_config = ConfigDict(from_attributes=True)


class GameBase(OrmSchema):
    """Shared game fields."""

    name: str
    type: str
    extension_of_id: Optional[int] = None
    creation_year: Optional[int] = None
    min_players: Optional[int] = None
    max_players: Optional[int] = None
    min_age: Optional[int] = None
    duration_minutes: Optional[int] = None
    url: Optional[str] = None
    image_url: Optional[str] = None


class GameCreate(GameBase):
    """Payload used to create a game."""

    authors: List[str] = Field(default_factory=list)
    artists: List[str] = Field(default_factory=list)
    editors: List[str] = Field(default_factory=list)
    distributors: List[str] = Field(default_factory=list)


class AuthorBase(OrmSchema):
    """Shared author fields."""

    name: str


class AuthorCreate(AuthorBase):
    """Payload used to create an author."""


class AuthorUpdate(AuthorBase):
    """Payload used to update an author."""


class Author(AuthorBase):
    """Author response schema."""

    id: int


class ArtistBase(OrmSchema):
    """Shared artist fields."""

    name: str


class ArtistCreate(ArtistBase):
    """Payload used to create an artist."""


class ArtistUpdate(ArtistBase):
    """Payload used to update an artist."""


class Artist(ArtistBase):
    """Artist response schema."""

    id: int


class EditorBase(OrmSchema):
    """Shared editor fields."""

    name: str


class EditorCreate(EditorBase):
    """Payload used to create an editor."""


class EditorUpdate(EditorBase):
    """Payload used to update an editor."""


class Editor(EditorBase):
    """Editor response schema."""

    id: int


class DistributorBase(OrmSchema):
    """Shared distributor fields."""

    name: str


class DistributorCreate(DistributorBase):
    """Payload used to create a distributor."""


class DistributorUpdate(DistributorBase):
    """Payload used to update a distributor."""


class Distributor(DistributorBase):
    """Distributor response schema."""

    id: int


class Game(GameBase):
    """Game response schema."""

    id: int
    authors: List[Author] = Field(default_factory=list)
    artists: List[Artist] = Field(default_factory=list)
    editors: List[Editor] = Field(default_factory=list)
    distributors: List[Distributor] = Field(default_factory=list)


class GamePage(OrmSchema):
    """Paginated game list response."""

    items: List[Game] = Field(default_factory=list)
    total: int
    skip: int
    limit: int


class VersionInfo(OrmSchema):
    """Application version metadata."""

    name: str
    version: str


class UserBase(OrmSchema):
    """Shared user fields."""

    email: str
    username: Optional[str] = None


class UserCreate(UserBase):
    """Payload used to create a user."""


class User(UserBase):
    """User response schema."""

    id: UUID


class CollectionGameBase(OrmSchema):
    """Shared collection game fields."""

    quantity: Optional[int] = 1


class CollectionGameCreate(CollectionGameBase):
    """Payload used to create a collection game."""

    collection_id: int
    game_id: int
    location_id: Optional[int] = None


class PersonalCollectionGameCreate(CollectionGameBase):
    """Payload used to add a game to the authenticated user's collection."""

    game_id: int
    location_id: Optional[int] = None


class CollectionGameUpdate(OrmSchema):
    """Payload used to update an existing collection game."""

    location_id: Optional[int] = None


class CollectionGame(CollectionGameBase):
    """Collection game response schema."""

    id: int
    collection_id: int
    game_id: int
    location_id: Optional[int] = None


class PersonalCollectionItem(CollectionGame):
    """Collection game enriched with the linked catalog game."""

    game: Game


class CollectionShareBase(OrmSchema):
    """Shared collection share fields."""

    permission: str


class CollectionShareCreate(CollectionShareBase):
    """Payload used to create a collection share."""

    shared_with: UUID


class CollectionShare(CollectionShareBase):
    """Collection share response schema."""

    id: int
    collection_id: int
    shared_with: UUID


class CollectionSubscriber(CollectionShare):
    """Subscriber granted access to a shared collection."""

    user: Optional[User] = None


class CollectionShareSettingsUpdate(OrmSchema):
    """Payload used to toggle or regenerate the personal collection share link."""

    share_enabled: Optional[bool] = None
    regenerate_link: bool = False


class CollectionShareSettings(OrmSchema):
    """Share settings for the authenticated user's collection."""

    collection_id: int
    share_enabled: bool
    share_token: Optional[str] = None
    subscribers: List[CollectionSubscriber] = Field(default_factory=list)


class CollectionShareJoinCreate(OrmSchema):
    """Payload used to join a shared collection through its invite link."""

    share_token: str


class CollectionBase(OrmSchema):
    """Shared collection fields."""

    name: str
    description: Optional[str] = None


class CollectionCreate(CollectionBase):
    """Payload used to create a collection."""

    owner_id: UUID


class Collection(CollectionBase):
    """Collection response schema."""

    id: int
    owner_id: UUID
    share_token: Optional[str] = None
    share_enabled: bool = False
    owner: Optional[User] = None
    games: List[CollectionGame] = Field(default_factory=list)
    shares: List[CollectionShare] = Field(default_factory=list)


class UserLocationBase(OrmSchema):
    """Shared user location fields."""

    name: str


class UserLocationCreate(UserLocationBase):
    """Payload used to create a user location."""

    user_id: UUID


class UserLocation(UserLocationBase):
    """User location response schema."""

    id: int
    user_id: UUID


class PersonalLocationCreate(UserLocationBase):
    """Payload used to create a location for the authenticated user."""


class PersonalLocationUpdate(UserLocationBase):
    """Payload used to rename a location for the authenticated user."""


class PersonalCollectionBoard(OrmSchema):
    """Authenticated user's collection grouped by locations."""

    collection_id: int
    locations: List[UserLocation] = Field(default_factory=list)
    items: List[PersonalCollectionItem] = Field(default_factory=list)


class SharedCollectionSummary(OrmSchema):
    """A collection the authenticated user can view through a share."""

    collection_id: int
    share_id: int
    permission: str
    name: str
    description: Optional[str] = None
    owner: Optional[User] = None
    game_count: int = 0


class SharedCollectionBoard(OrmSchema):
    """Read-only board for a shared collection owned by another user."""

    collection_id: int
    share_id: int
    permission: str
    name: str
    description: Optional[str] = None
    owner: Optional[User] = None
    locations: List[UserLocation] = Field(default_factory=list)
    items: List[PersonalCollectionItem] = Field(default_factory=list)
