from backend.app import main
from backend.app import auth
from types import SimpleNamespace


def test_app_registers_game_routes():
    paths = {route.path for route in main.app.routes}

    assert "/api/games/" in paths
    assert "/api/meta/version/" in paths
    assert "/api/users/" in paths
    assert "/api/collections/" in paths
    assert "/api/me/collection/games/" in paths
    assert "/api/me/collection/board/" in paths
    assert "/api/me/collection/share/" in paths
    assert "/api/me/collection/share/join/" in paths
    assert "/api/me/friends/collections/" in paths
    assert "/api/me/friends/collections/{collection_id}/board/" in paths
    assert "/api/authors/{author_id}" in paths


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


def test_update_author_delegates_to_crud(monkeypatch):
    captured = {}

    def fake_update_author(**kwargs):
        captured.update(kwargs)
        return {"id": kwargs["author_id"], "name": kwargs["author"].name}

    monkeypatch.setattr(main.crud, "update_author", fake_update_author)

    response = main.update_author(
        author_id=4,
        author=main.schemas.AuthorUpdate(name="Renamed Author"),
    )

    assert response == {"id": 4, "name": "Renamed Author"}
    assert captured == {
        "author_id": 4,
        "author": main.schemas.AuthorUpdate(name="Renamed Author"),
    }


def test_admin_email_is_case_insensitive():
    assert auth.is_admin_user({"email": "RENAULT.JBAPT@GMAIL.COM"})
    assert not auth.is_admin_user({"email": "alice@example.com"})
    assert not auth.is_admin_user({})


def test_admin_guard_allows_personal_collection_and_catalog_reads():
    assert not auth.requires_admin_access("/api/me/collection/games/", "POST")
    assert not auth.requires_admin_access("/api/me/collection/locations/", "POST")
    assert not auth.requires_admin_access("/api/me/collection/locations/4", "PATCH")
    assert not auth.requires_admin_access("/api/me/collection/locations/4", "DELETE")
    assert not auth.requires_admin_access("/api/me/collection/share/", "PATCH")
    assert not auth.requires_admin_access("/api/me/friends/collections/1/subscription/", "DELETE")
    assert not auth.requires_admin_access("/api/games/", "GET")
    assert not auth.requires_admin_access("/api/authors/1", "GET")


def test_admin_guard_protects_global_catalog_writes_and_legacy_collection_routes():
    assert auth.requires_admin_access("/api/games/", "POST")
    assert auth.requires_admin_access("/api/games/1", "DELETE")
    assert auth.requires_admin_access("/api/authors/", "POST")
    assert auth.requires_admin_access("/api/authors/1", "PATCH")
    assert auth.requires_admin_access("/api/collections/", "GET")
    assert auth.requires_admin_access("/api/collection_games/1", "DELETE")


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
        "location_id": None,
    }


def test_get_my_collection_board_delegates_to_crud(monkeypatch):
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_get_personal_collection_board(**kwargs):
        assert kwargs == {"auth_user": {"name": "Alice", "email": "alice@example.com"}}
        return {"collection_id": 1, "locations": [], "items": []}

    monkeypatch.setattr(main.crud, "get_personal_collection_board", fake_get_personal_collection_board)

    response = main.get_my_collection_board(request=request)

    assert response["collection_id"] == 1


def test_get_my_collection_share_settings_delegates_to_crud(monkeypatch):
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_get_personal_collection_share_settings(**kwargs):
        assert kwargs == {"auth_user": {"name": "Alice", "email": "alice@example.com"}}
        return {"collection_id": 1, "share_enabled": False, "share_token": None, "subscribers": []}

    monkeypatch.setattr(main.crud, "get_personal_collection_share_settings", fake_get_personal_collection_share_settings)

    response = main.get_my_collection_share_settings(request=request)

    assert response["collection_id"] == 1


def test_update_my_collection_share_settings_delegates_to_crud(monkeypatch):
    captured = {}
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_update_personal_collection_share_settings(**kwargs):
        captured.update(kwargs)
        return {"collection_id": 1, "share_enabled": True, "share_token": "token", "subscribers": []}

    monkeypatch.setattr(main.crud, "update_personal_collection_share_settings", fake_update_personal_collection_share_settings)

    response = main.update_my_collection_share_settings(
        request=request,
        payload=main.schemas.CollectionShareSettingsUpdate(share_enabled=True, regenerate_link=True),
    )

    assert response["share_enabled"] is True
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "share_enabled": True,
        "regenerate_link": True,
    }


def test_join_collection_share_delegates_to_crud(monkeypatch):
    captured = {}
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_join_shared_collection(**kwargs):
        captured.update(kwargs)
        return {
            "collection_id": 9,
            "share_id": 4,
            "permission": "viewer",
            "name": "Collection de Bob",
            "description": None,
            "owner": {"id": "abc", "email": "bob@example.com", "username": "Bob"},
            "game_count": 12,
        }

    monkeypatch.setattr(main.crud, "join_shared_collection", fake_join_shared_collection)

    response = main.join_collection_share(
        request=request,
        payload=main.schemas.CollectionShareJoinCreate(share_token="share-token"),
    )

    assert response["collection_id"] == 9
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "share_token": "share-token",
    }


def test_get_my_friend_collections_delegates_to_crud(monkeypatch):
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_get_shared_collections(**kwargs):
        assert kwargs == {"auth_user": {"name": "Alice", "email": "alice@example.com"}}
        return []

    monkeypatch.setattr(main.crud, "get_shared_collections", fake_get_shared_collections)

    assert main.get_my_friend_collections(request=request) == []


def test_get_my_friend_collection_board_delegates_to_crud(monkeypatch):
    captured = {}
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_get_shared_collection_board(**kwargs):
        captured.update(kwargs)
        return {
            "collection_id": kwargs["collection_id"],
            "share_id": 4,
            "permission": "viewer",
            "name": "Collection de Bob",
            "description": None,
            "owner": {"id": "abc", "email": "bob@example.com", "username": "Bob"},
            "locations": [],
            "items": [],
        }

    monkeypatch.setattr(main.crud, "get_shared_collection_board", fake_get_shared_collection_board)

    response = main.get_my_friend_collection_board(request=request, collection_id=9)

    assert response["collection_id"] == 9
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "collection_id": 9,
    }


def test_unsubscribe_from_friend_collection_delegates_to_crud(monkeypatch):
    captured = {}
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_unsubscribe_from_shared_collection(**kwargs):
        captured.update(kwargs)
        return {"id": 2, "collection_id": kwargs["collection_id"], "shared_with": "abc", "permission": "viewer"}

    monkeypatch.setattr(main.crud, "unsubscribe_from_shared_collection", fake_unsubscribe_from_shared_collection)

    response = main.unsubscribe_from_friend_collection(request=request, collection_id=11)

    assert response["collection_id"] == 11
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "collection_id": 11,
    }


def test_move_game_in_my_collection_delegates_to_crud(monkeypatch):
    captured = {}
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_move_personal_collection_game(**kwargs):
        captured.update(kwargs)
        return {"id": 3, "collection_id": 2, "game_id": 4, "location_id": 9, "quantity": 1}

    monkeypatch.setattr(main.crud, "move_personal_collection_game", fake_move_personal_collection_game)

    response = main.move_game_in_my_collection(
        request=request,
        collection_game_id=3,
        payload=main.schemas.CollectionGameUpdate(location_id=9),
    )

    assert response["location_id"] == 9
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "collection_game_id": 3,
        "location_id": 9,
    }


def test_remove_game_from_my_collection_delegates_to_crud(monkeypatch):
    captured = {}
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_remove_game_from_personal_collection(**kwargs):
        captured.update(kwargs)
        return {"id": 3, "collection_id": 2, "game_id": 4, "location_id": None, "quantity": 1}

    monkeypatch.setattr(main.crud, "remove_game_from_personal_collection", fake_remove_game_from_personal_collection)

    response = main.remove_game_from_my_collection(request=request, collection_game_id=3)

    assert response["id"] == 3
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "collection_game_id": 3,
    }


def test_create_location_in_my_collection_delegates_to_crud(monkeypatch):
    captured = {}
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_create_personal_location(**kwargs):
        captured.update(kwargs)
        return {"id": 2, "user_id": "abc", "name": "Chambre"}

    monkeypatch.setattr(main.crud, "create_personal_location", fake_create_personal_location)

    response = main.create_location_in_my_collection(
        request=request,
        payload=main.schemas.PersonalLocationCreate(name="Chambre"),
    )

    assert response["name"] == "Chambre"
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "name": "Chambre",
    }


def test_update_location_in_my_collection_delegates_to_crud(monkeypatch):
    captured = {}
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_update_personal_location(**kwargs):
        captured.update(kwargs)
        return {"id": kwargs["location_id"], "user_id": "abc", "name": kwargs["name"]}

    monkeypatch.setattr(main.crud, "update_personal_location", fake_update_personal_location)

    response = main.update_location_in_my_collection(
        request=request,
        location_id=7,
        payload=main.schemas.PersonalLocationUpdate(name="Salon"),
    )

    assert response["name"] == "Salon"
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "location_id": 7,
        "name": "Salon",
    }


def test_delete_location_in_my_collection_delegates_to_crud(monkeypatch):
    captured = {}
    request = SimpleNamespace(state=SimpleNamespace(user={"name": "Alice", "email": "alice@example.com"}))

    def fake_delete_personal_location(**kwargs):
        captured.update(kwargs)
        return {"id": kwargs["location_id"], "user_id": "abc", "name": "Salon"}

    monkeypatch.setattr(main.crud, "delete_personal_location", fake_delete_personal_location)

    response = main.delete_location_in_my_collection(request=request, location_id=7)

    assert response["id"] == 7
    assert captured == {
        "auth_user": {"name": "Alice", "email": "alice@example.com"},
        "location_id": 7,
    }
