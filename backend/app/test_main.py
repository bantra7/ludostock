import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import Header
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker


TEST_DB_MARKER = Path(__file__).with_name("test_backend.duckdb")
TEST_DB_MARKER.touch(exist_ok=True)
os.environ.setdefault("DATABASE_URL", f"duckdb:///{TEST_DB_MARKER.as_posix()}")
os.environ.setdefault("SQL_CREATION_FILE", str(Path(__file__).with_name("test_schema.sql")))
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")

from backend.app.main import app, get_db, verify_supabase_token
from backend.app.database import Base
from backend.app import models


TEST_SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_tables_once():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def cleanup_db():
    db = TestingSessionLocal()
    try:
        db.query(models.CollectionGame).delete()
        db.query(models.CollectionShare).delete()
        db.query(models.UserLocation).delete()
        db.query(models.Collection).delete()
        db.query(models.User).delete()
        db.query(models.Game).delete()
        db.query(models.Author).delete()
        db.query(models.Artist).delete()
        db.query(models.Editor).delete()
        db.query(models.Distributor).delete()
        db.commit()
        yield
    finally:
        db.close()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_verify_supabase_token(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return {"id": str(uuid4())}
    return {"id": authorization.split(" ", 1)[1]}


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[verify_supabase_token] = override_verify_supabase_token
client = TestClient(app)


def test_create_user_generates_uuid():
    response = client.post(
        "/api/users/",
        json={"email": "alice@example.com", "username": "alice"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"
    assert data["id"]


def test_create_author_duplicate_returns_conflict():
    first = client.post("/api/authors/", json={"name": "Reiner Knizia"})
    second = client.post("/api/authors/", json={"name": "Reiner Knizia"})

    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"] == "Author with this name already exists"


def test_create_game_is_atomic_on_duplicate_related_entities():
    client.post("/api/authors/", json={"name": "Existing Author"})

    response = client.post(
        "/api/games/",
        json={
            "name": "Broken Game",
            "type": "base",
            "authors": ["New Author", "Existing Author", "New Author"],
        },
    )

    assert response.status_code == 409

    authors = client.get("/api/authors/")
    author_names = sorted(author["name"] for author in authors.json())
    assert author_names == ["Existing Author"]


def test_delete_collection_game_returns_deleted_object():
    user_response = client.post(
        "/api/users/",
        json={"email": "owner@example.com", "username": "owner"},
    )
    assert user_response.status_code == 200
    owner_id = user_response.json()["id"]

    collection_response = client.post(
        "/api/collections/",
        headers={"Authorization": f"Bearer {owner_id}"},
        json={"name": "Main", "description": "Primary collection"},
    )
    assert collection_response.status_code == 200

    game_response = client.post(
        "/api/games/",
        json={"name": "Azul", "type": "base"},
    )
    assert game_response.status_code == 200

    collection_game_response = client.post(
        "/api/collection_games/",
        json={
            "collection_id": collection_response.json()["id"],
            "game_id": game_response.json()["id"],
            "quantity": 2,
        },
    )
    assert collection_game_response.status_code == 200

    delete_response = client.delete(
        f"/api/collection_games/{collection_game_response.json()['id']}"
    )

    assert delete_response.status_code == 200
    deleted = delete_response.json()
    assert deleted["id"] == collection_game_response.json()["id"]
    assert deleted["quantity"] == 2


def test_collection_share_requires_owner():
    owner_response = client.post(
        "/api/users/",
        json={"email": "owner2@example.com", "username": "owner2"},
    )
    other_response = client.post(
        "/api/users/",
        json={"email": "other@example.com", "username": "other"},
    )
    target_response = client.post(
        "/api/users/",
        json={"email": "target@example.com", "username": "target"},
    )

    collection_response = client.post(
        "/api/collections/",
        headers={"Authorization": f"Bearer {owner_response.json()['id']}"},
        json={"name": "Shared", "description": None},
    )

    forbidden_response = client.post(
        f"/api/collection_shares/?collection_id={collection_response.json()['id']}",
        headers={"Authorization": f"Bearer {other_response.json()['id']}"},
        json={"shared_with": target_response.json()["id"], "permission": "read"},
    )

    assert forbidden_response.status_code == 403
    assert forbidden_response.json()["detail"] == "Only the collection owner can share it"
