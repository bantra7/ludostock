import os
from argparse import Namespace

from backend.app import import_games
from backend.app.import_games import build_game_payload


def test_build_game_payload_normalizes_csv_fields():
    payload = build_game_payload(
        {
            "nom": "7 Wonders Duel",
            "type": "Jeu",
            "annee_de_sortie": "2015",
            "nombre_de_joueurs": "2",
            "age": "10+",
            "duree_de_partie": "30 min",
            "url": "https://example.test/game",
            "url_image": "https://example.test/game.png",
            "auteurs": "Antoine Bauza; Bruno Cathala",
            "artistes": "Miguel Coimbra",
            "editeurs": "Repos Production / Asmodee",
            "distributeurs": "Asmodee",
        }
    )

    assert payload is not None
    assert payload.name == "7 Wonders Duel"
    assert payload.type == "jeu"
    assert payload.creation_year == 2015
    assert payload.min_players == 2
    assert payload.max_players == 2
    assert payload.min_age == 10
    assert payload.duration_minutes == 30
    assert payload.authors == ["Antoine Bauza", "Bruno Cathala"]
    assert payload.editors == ["Repos Production", "Asmodee"]


def test_build_game_payload_returns_none_without_name():
    assert build_game_payload({"nom": "   "}) is None


def test_parse_args_accepts_env_path():
    args = import_games.parse_args(["--env-path", "backend/.env.local", "--limit", "10"])

    assert args.env_path == "backend/.env.local"
    assert args.limit == 10


def test_resolve_env_path_raises_for_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(import_games, "DEFAULT_ENV_CANDIDATES", (tmp_path / ".env",))

    try:
        import_games.resolve_env_path("backend/.env.local")
    except FileNotFoundError as exc:
        assert "Fichier d'environnement introuvable" in str(exc)
    else:
        raise AssertionError("resolve_env_path should fail when the env file is missing")


def test_main_sets_env_path_before_import(monkeypatch, tmp_path):
    csv_path = tmp_path / "games.csv"
    csv_path.write_text("nom\nAzul\n", encoding="utf-8")
    env_path = tmp_path / ".env"
    env_path.write_text("SQLITE_PATH=backend/app/test.db\n", encoding="utf-8")

    monkeypatch.setattr(
        import_games,
        "parse_args",
        lambda argv=None: Namespace(
            env_path=str(env_path),
            csv_path=str(csv_path),
            limit=1,
        ),
    )

    captured = {}

    def fake_import_games(csv_path, limit):
        captured["env_path"] = os.environ.get("ENV_PATH")
        captured["csv_path"] = csv_path
        captured["limit"] = limit
        return 1, 0

    monkeypatch.setattr(import_games, "import_games", fake_import_games)

    import_games.main()

    assert captured["env_path"] == str(env_path)
    assert captured["csv_path"] == str(csv_path)
    assert captured["limit"] == 1


def test_main_uses_default_env_candidate(monkeypatch, tmp_path):
    csv_path = tmp_path / "games.csv"
    csv_path.write_text("nom\nAzul\n", encoding="utf-8")
    env_path = tmp_path / ".env"
    env_path.write_text("SQLITE_PATH=backend/app/test.db\n", encoding="utf-8")

    monkeypatch.setattr(import_games, "DEFAULT_ENV_CANDIDATES", (env_path,))
    monkeypatch.setattr(
        import_games,
        "parse_args",
        lambda argv=None: Namespace(
            env_path=None,
            csv_path=str(csv_path),
            limit=1,
        ),
    )

    captured = {}

    def fake_import_games(csv_path, limit):
        captured["env_path"] = os.environ.get("ENV_PATH")
        captured["csv_path"] = csv_path
        captured["limit"] = limit
        return 1, 0

    monkeypatch.setattr(import_games, "import_games", fake_import_games)

    import_games.main()

    assert captured["env_path"] == str(env_path)
    assert captured["csv_path"] == str(csv_path)
    assert captured["limit"] == 1
