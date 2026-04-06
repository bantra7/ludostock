"""Tests for the root CSV import script."""

from pathlib import Path

import pytest

import import_data


def test_row_to_game_payload_parses_core_fields():
    row = {
        "Url": "https://trictrac.net/jeu-de-societe/azul",
        "Nom": "Azul",
        "Type": "Jeu",
        "Année de sortie": "2017",
        "Nombre de joueurs": "2 - 4",
        "Age": "8 ans et +",
        "Durée de partie": "45 min",
        "Url Image": "https://example.com/azul.webp",
        "Auteurs": "Michael Kiesling / Michael Kiesling",
        "Artistes": "Philippe Guérin",
        "Editeurs": "Next Move",
        "Distributeurs": "Asmodee",
    }

    prepared = import_data.row_to_game_payload(row, enrichment=None)

    assert prepared.payload.name == "Azul"
    assert prepared.payload.type == "jeu"
    assert prepared.payload.creation_year == 2017
    assert prepared.payload.min_players == 2
    assert prepared.payload.max_players == 4
    assert prepared.payload.min_age == 8
    assert prepared.payload.duration_minutes == 45
    assert prepared.payload.authors == ["Michael Kiesling"]
    assert prepared.payload.artists == ["Philippe Guérin"]
    assert prepared.payload.editors == ["Next Move"]
    assert prepared.payload.distributors == ["Asmodee"]


def test_prepare_games_refuses_rows_without_relations():
    row = {
        "Url": "https://trictrac.net/jeu-de-societe/azul",
        "Nom": "Azul",
        "Type": "Jeu",
        "Année de sortie": "2017",
        "Nombre de joueurs": "2 - 4",
        "Age": "8 ans et +",
        "Durée de partie": "45 min",
        "Url Image": "https://example.com/azul.webp",
        "Auteurs": "",
        "Artistes": "",
        "Editeurs": "",
        "Distributeurs": "",
    }

    with pytest.raises(ValueError, match="aucun contributeur exploitable"):
        import_data.prepare_games([row], enrichments={}, allow_missing_relations=False)


def test_insert_games_and_link_extensions_create_relations(tmp_path: Path):
    base_row = {
        "Url": "https://trictrac.net/jeu-de-societe/azul",
        "Nom": "Azul",
        "Type": "Jeu",
        "Année de sortie": "2017",
        "Nombre de joueurs": "2 - 4",
        "Age": "8 ans et +",
        "Durée de partie": "45 min",
        "Url Image": "https://example.com/azul.webp",
        "Auteurs": "Michael Kiesling",
        "Artistes": "Philippe Guérin",
        "Editeurs": "Next Move",
        "Distributeurs": "Asmodee",
    }
    extension_row = {
        "Url": "https://trictrac.net/jeu-de-societe/azul-extension",
        "Nom": "Azul : Extension Cristal",
        "Type": "Extension",
        "Année de sortie": "2018",
        "Nombre de joueurs": "2 - 4",
        "Age": "8 ans et +",
        "Durée de partie": "15 min",
        "Url Image": "https://example.com/azul-extension.webp",
        "Auteurs": "Michael Kiesling",
        "Artistes": "Philippe Guérin",
        "Editeurs": "Next Move",
        "Distributeurs": "Asmodee",
    }

    games = import_data.prepare_games(
        [base_row, extension_row],
        enrichments={},
        allow_missing_relations=False,
    )

    db_path = tmp_path / "ludostock.db"
    connection = import_data.recreate_database(db_path, force=False)
    try:
        import_data.insert_games(connection, games)
        linked_extensions = import_data.link_extensions(connection, games)

        counts = import_data.summarize_database(connection)
        extension_row_db = connection.execute(
            "SELECT extension_of_id FROM games WHERE name = ?",
            ("Azul : Extension Cristal",),
        ).fetchone()
    finally:
        connection.close()

    assert linked_extensions == 1
    assert counts["games"] == 2
    assert counts["authors"] == 1
    assert counts["artists"] == 1
    assert counts["editors"] == 1
    assert counts["distributors"] == 1
    assert counts["game_authors"] == 2
    assert extension_row_db["extension_of_id"] == games[0].database_id
