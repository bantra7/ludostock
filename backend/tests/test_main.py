from backend.app import main


def test_app_registers_game_routes():
    paths = {route.path for route in main.app.routes}

    assert "/api/games/" in paths
    assert "/api/users/" in paths
    assert "/api/collections/" in paths
