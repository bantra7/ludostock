from backend.app import main


def test_app_registers_game_routes():
    paths = {route.path for route in main.app.routes}

    assert "/api/games/" in paths
    assert "/api/users/" in paths
    assert "/api/collections/" in paths


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
