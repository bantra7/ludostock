from backend.app import main
from types import SimpleNamespace


def test_app_registers_game_routes():
    paths = {route.path for route in main.app.routes}

    assert "/api/games/" in paths
    assert "/api/meta/version/" in paths
    assert "/api/users/" in paths
    assert "/api/collections/" in paths
    assert "/api/me/collection/games/" in paths


def test_get_games_delegates_to_paginated_crud(monkeypatch):
    captured = {}

    def fake_get_games_page(**kwargs):
        captured.update(kwargs)
        return {"items": [], "total": 0, "skip": kwargs["skip"], "limit": kwargs["limit"]}

    monkeypatch.setattr(main.crud, "get_games_page", fake_get_games_page)

    response = main.get_games(
        skip=20,
        limit=50,
        search="azul",
        game_type="jeu",
        year="2017",
        sort_by="authors",
        sort_dir="desc",
    )

    assert response["total"] == 0
    assert captured == {
        "skip": 20,
        "limit": 50,
        "search": "azul",
        "game_type": "jeu",
        "year": "2017",
        "sort_by": "authors",
        "sort_dir": "desc",
    }


def test_get_version_returns_backend_metadata():
    response = main.get_version()

    assert response == {"name": "backend", "version": main.__version__}


def test_get_my_collection_games_delegates_to_personal_collection_crud(monkeypatch):
    captured = {}

    def fake_get_personal_collection_games(**kwargs):
        captured.update(kwargs)
        return {"items": [], "total": 0, "skip": kwargs["skip"], "limit": kwargs["limit"]}

    monkeypatch.setattr(main.crud, "get_personal_collection_games", fake_get_personal_collection_games)
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    response = main.get_my_collection_games(
        request=request,
        skip=10,
        limit=25,
        search="azul",
        game_type="jeu",
        year="2017",
        sort_by="name",
        sort_dir="asc",
    )

    assert response["total"] == 0
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "skip": 10,
        "limit": 25,
        "search": "azul",
        "game_type": "jeu",
        "year": "2017",
        "sort_by": "name",
        "sort_dir": "asc",
    }


def test_add_game_to_my_collection_delegates_to_crud(monkeypatch):
    captured = {}

    def fake_add_game_to_personal_collection(**kwargs):
        captured.update(kwargs)
        return {"id": 1, "collection_id": 2, "game_id": kwargs["game_id"], "location_id": None, "quantity": 1}

    monkeypatch.setattr(main.crud, "add_game_to_personal_collection", fake_add_game_to_personal_collection)
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    response = main.add_game_to_my_collection(
        request=request,
        payload=main.schemas.PersonalCollectionGameCreate(game_id=42, quantity=1),
    )

    assert response["game_id"] == 42
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "game_id": 42,
        "quantity": 1,
    }
