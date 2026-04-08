import sqlite3

import pytest
from fastapi import HTTPException

from backend.app import crud, database, schemas


def test_raise_write_error_maps_unique_to_409():
    exc = sqlite3.IntegrityError("UNIQUE constraint failed: authors.name")

    with pytest.raises(HTTPException) as exc_info:
        crud._raise_write_error(exc, "Author with this name already exists")

    assert exc_info.value.status_code == 409


def test_raise_write_error_maps_foreign_key_to_400():
    exc = sqlite3.IntegrityError("FOREIGN KEY constraint failed")

    with pytest.raises(HTTPException) as exc_info:
        crud._raise_write_error(exc, "Collection could not be created")

    assert exc_info.value.status_code == 400


@pytest.fixture
def sqlite_game_store(tmp_path, monkeypatch):
    database_path = tmp_path / "games.db"

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        for statement in database.SCHEMA_STATEMENTS:
            connection.execute(statement)
        connection.commit()

    def temp_get_connection():
        connection = sqlite3.connect(database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    monkeypatch.setattr(crud, "get_connection", temp_get_connection)
    return database_path


def test_get_games_page_returns_total_and_requested_slice(sqlite_game_store):
    crud.create_game(
        schemas.GameCreate(name="Azul", type="jeu", authors=["Michael Kiesling"], editors=["Next Move"])
    )
    crud.create_game(
        schemas.GameCreate(name="Patchwork", type="jeu", authors=["Uwe Rosenberg"], editors=["Lookout Games"])
    )
    crud.create_game(
        schemas.GameCreate(name="Carcassonne", type="jeu", authors=["Klaus-Jurgen Wrede"], editors=["Hans im Gluck"])
    )

    page = crud.get_games_page(skip=1, limit=1)

    assert page["total"] == 3
    assert page["skip"] == 1
    assert page["limit"] == 1
    assert [game["name"] for game in page["items"]] == ["Carcassonne"]


def test_get_games_page_filters_by_search_type_and_year(sqlite_game_store):
    crud.create_game(
        schemas.GameCreate(
            name="Azul",
            type="jeu",
            creation_year=2017,
            authors=["Michael Kiesling"],
            editors=["Next Move"],
        )
    )
    crud.create_game(
        schemas.GameCreate(
            name="Azul Duel",
            type="extension",
            creation_year=2025,
            authors=["Bruno Cathala"],
            editors=["Space Cow"],
        )
    )
    crud.create_game(
        schemas.GameCreate(
            name="Patchwork",
            type="jeu",
            creation_year=2014,
            authors=["Uwe Rosenberg"],
            editors=["Lookout Games"],
        )
    )

    page = crud.get_games_page(
        skip=0,
        limit=10,
        search="azul",
        game_type="Jeu",
        year="2017",
    )

    assert page["total"] == 1
    assert [game["name"] for game in page["items"]] == ["Azul"]


def test_get_games_page_sorts_by_author_and_numeric_fields(sqlite_game_store):
    crud.create_game(
        schemas.GameCreate(
            name="Cascadia",
            type="jeu",
            min_players=1,
            max_players=4,
            duration_minutes=45,
            authors=["Randy Flynn"],
            editors=["AEG"],
        )
    )
    crud.create_game(
        schemas.GameCreate(
            name="Azul",
            type="jeu",
            min_players=2,
            max_players=4,
            duration_minutes=30,
            authors=["Michael Kiesling"],
            editors=["Next Move"],
        )
    )
    crud.create_game(
        schemas.GameCreate(
            name="Patchwork",
            type="jeu",
            min_players=2,
            max_players=2,
            duration_minutes=15,
            authors=["Uwe Rosenberg"],
            editors=["Lookout Games"],
        )
    )

    author_sorted_page = crud.get_games_page(skip=0, limit=10, sort_by="authors", sort_dir="desc")
    duration_sorted_page = crud.get_games_page(skip=0, limit=10, sort_by="duration_minutes", sort_dir="asc")

    assert [game["name"] for game in author_sorted_page["items"]] == ["Patchwork", "Cascadia", "Azul"]
    assert [game["name"] for game in duration_sorted_page["items"]] == ["Patchwork", "Azul", "Cascadia"]


def test_get_personal_collection_games_creates_user_collection_and_filters(sqlite_game_store):
    azul = crud.create_game(
        schemas.GameCreate(name="Azul", type="jeu", authors=["Michael Kiesling"], editors=["Next Move"])
    )
    patchwork = crud.create_game(
        schemas.GameCreate(name="Patchwork", type="jeu", authors=["Uwe Rosenberg"], editors=["Lookout Games"])
    )

    auth_user = {"name": "Alice Example", "email": "alice@example.com"}

    crud.add_game_to_personal_collection(auth_user=auth_user, game_id=azul["id"])
    crud.add_game_to_personal_collection(auth_user=auth_user, game_id=patchwork["id"])

    page = crud.get_personal_collection_games(
        auth_user=auth_user,
        skip=0,
        limit=10,
        search="patch",
        sort_by="name",
        sort_dir="asc",
    )

    users = crud.get_users()
    collections = crud.get_collections()

    assert len(users) == 1
    assert users[0]["username"] == "Alice Example"
    assert len(collections) == 1
    assert collections[0]["name"] == "Collection de Alice Example"
    assert page["total"] == 1
    assert [game["name"] for game in page["items"]] == ["Patchwork"]


def test_add_game_to_personal_collection_rejects_duplicate_game(sqlite_game_store):
    azul = crud.create_game(
        schemas.GameCreate(name="Azul", type="jeu", authors=["Michael Kiesling"], editors=["Next Move"])
    )
    auth_user = {"name": "Alice Example", "email": "alice@example.com"}

    crud.add_game_to_personal_collection(auth_user=auth_user, game_id=azul["id"])

    with pytest.raises(HTTPException) as exc_info:
        crud.add_game_to_personal_collection(auth_user=auth_user, game_id=azul["id"])

    assert exc_info.value.status_code == 409


def test_get_personal_collection_board_groups_items_and_locations(sqlite_game_store):
    azul = crud.create_game(
        schemas.GameCreate(name="Azul", type="jeu", authors=["Michael Kiesling"], editors=["Next Move"])
    )
    patchwork = crud.create_game(
        schemas.GameCreate(name="Patchwork", type="jeu", authors=["Uwe Rosenberg"], editors=["Lookout Games"])
    )
    auth_user = {"name": "Alice Example", "email": "alice@example.com"}

    location = crud.create_personal_location(auth_user=auth_user, name="Chambre")
    crud.add_game_to_personal_collection(auth_user=auth_user, game_id=azul["id"], location_id=location["id"])
    crud.add_game_to_personal_collection(auth_user=auth_user, game_id=patchwork["id"])

    board = crud.get_personal_collection_board(auth_user=auth_user)

    assert board["collection_id"] > 0
    assert [entry["name"] for entry in board["locations"]] == ["Chambre"]
    assert len(board["items"]) == 2
    assert {item["game"]["name"] for item in board["items"]} == {"Azul", "Patchwork"}
    azul_item = next(item for item in board["items"] if item["game"]["name"] == "Azul")
    patchwork_item = next(item for item in board["items"] if item["game"]["name"] == "Patchwork")
    assert azul_item["location_id"] == location["id"]
    assert patchwork_item["location_id"] is None


def test_move_personal_collection_game_updates_location(sqlite_game_store):
    azul = crud.create_game(
        schemas.GameCreate(name="Azul", type="jeu", authors=["Michael Kiesling"], editors=["Next Move"])
    )
    auth_user = {"name": "Alice Example", "email": "alice@example.com"}

    location = crud.create_personal_location(auth_user=auth_user, name="Maison 2")
    collection_game = crud.add_game_to_personal_collection(auth_user=auth_user, game_id=azul["id"])

    moved = crud.move_personal_collection_game(
        auth_user=auth_user,
        collection_game_id=collection_game["id"],
        location_id=location["id"],
    )

    assert moved["id"] == collection_game["id"]
    assert moved["location_id"] == location["id"]
