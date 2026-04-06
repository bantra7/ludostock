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
    assert [game["name"] for game in page["items"]] == ["Patchwork"]


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
        search="michael",
        game_type="Jeu",
        year="2017",
    )

    assert page["total"] == 1
    assert [game["name"] for game in page["items"]] == ["Azul"]
