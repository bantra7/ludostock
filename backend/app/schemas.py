from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

# ============================
# GAME SCHEMAS
# ============================
class GameBase(BaseModel):
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
    authors: Optional[List[str]] = []
    artists: Optional[List[str]] = []
    editors: Optional[List[str]] = []
    distributors: Optional[List[str]] = []

class Game(GameBase):
    id: int
    authors: List["Author"] = []
    artists: List["Artist"] = []
    editors: List["Editor"] = []
    distributors: List["Distributor"] = []

    class Config:
        from_attributes = True

# ============================
# LINKED TABLES SCHEMAS
# ============================
class AuthorBase(BaseModel):
    name: str

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: int
    class Config:
        from_attributes = True

class ArtistBase(BaseModel):
    name: str

class ArtistCreate(ArtistBase):
    pass

class Artist(ArtistBase):
    id: int
    class Config:
        from_attributes = True

class EditorBase(BaseModel):
    name: str

class EditorCreate(EditorBase):
    pass

class Editor(EditorBase):
    id: int
    class Config:
        from_attributes = True

class DistributorBase(BaseModel):
    name: str

class DistributorCreate(DistributorBase):
    pass

class Distributor(DistributorBase):
    id: int
    class Config:
        from_attributes = True

# ============================
# USER SCHEMAS
# ============================
class UserBase(BaseModel):
    email: str
    username: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: UUID
    class Config:
        from_attributes = True

# ============================
# COLLECTION SCHEMAS
# ============================
class CollectionBase(BaseModel):
    name: str
    description: Optional[str] = None

class CollectionCreate(CollectionBase):
    pass

class Collection(CollectionBase):
    id: int
    owner_id: UUID
    owner: Optional[User] = None
    games: List["CollectionGame"] = []
    shares: List["CollectionShare"] = []

    class Config:
        from_attributes = True

# ============================
# COLLECTION SHARE SCHEMAS
# ============================
class CollectionShareBase(BaseModel):
    permission: str

class CollectionShareCreate(CollectionShareBase):
    shared_with: UUID

class CollectionShare(CollectionShareBase):
    id: int
    collection_id: int
    shared_with: UUID

    class Config:
        from_attributes = True

# ============================
# USER LOCATION SCHEMAS
# ============================
class UserLocationBase(BaseModel):
    name: str

class UserLocationCreate(UserLocationBase):
    pass

class UserLocation(UserLocationBase):
    id: int
    user_id: UUID

    class Config:
        from_attributes = True

# ============================
# COLLECTION GAME SCHEMAS
# ============================
class CollectionGameBase(BaseModel):
    quantity: Optional[int] = 1

class CollectionGameCreate(CollectionGameBase):
    collection_id: int
    game_id: int
    location_id: Optional[int] = None

class CollectionGame(CollectionGameBase):
    id: int
    collection_id: int
    game_id: int
    location_id: Optional[int] = None

    class Config:
        from_attributes = True

# Pour les relations imbriquées, il faut ajouter ceci à la fin du fichier :