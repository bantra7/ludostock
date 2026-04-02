"""Import board games from a CSV file into the local SQLite database."""

import argparse
import csv
import os
from pathlib import Path
from typing import Iterable


DEFAULT_ENV_CANDIDATES = (
    Path("backend/app/.env"),
    Path("backend/.env"),
    Path(".env"),
)


def _split_names(value: str, separators: Iterable[str]) -> list[str]:
    """Split a contributor field with multiple possible separators."""
    values = [value]
    for separator in separators:
        next_values: list[str] = []
        for item in values:
            next_values.extend(item.split(separator))
        values = next_values
    return [item.strip() for item in values if item.strip()]


def _first_value(row: dict, *keys: str) -> str:
    """Return the first non-empty value found for the provided keys."""
    for key in keys:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _parse_players(value: str) -> tuple[int | None, int | None]:
    """Parse a player count such as `2` or `2-4`."""
    stripped = value.strip().replace(" a ", "-").replace(" à ", "-").replace(" - ", "-")
    if not stripped:
        return None, None
    if "-" in stripped:
        min_players, max_players = stripped.split("-", 1)
        return _parse_first_int(min_players), _parse_first_int(max_players)
    parsed_value = _parse_first_int(stripped)
    return parsed_value, parsed_value


def _parse_first_int(value: str) -> int | None:
    """Extract the first integer found in a string."""
    digits = "".join(character if character.isdigit() else " " for character in value)
    for part in digits.split():
        return int(part)
    return None


def build_game_payload(row: dict):
    """Build a `GameCreate` payload from a CSV row."""
    from . import schemas

    name = _first_value(row, "nom", "Nom")
    if not name:
        return None

    min_players, max_players = _parse_players(
        _first_value(row, "nombre_de_joueurs", "Nombre de joueurs")
    )

    return schemas.GameCreate(
        name=name,
        type=_first_value(row, "type", "Type").lower() or "game",
        creation_year=_parse_first_int(_first_value(row, "annee_de_sortie", "Année de sortie")),
        min_players=min_players,
        max_players=max_players,
        min_age=_parse_first_int(_first_value(row, "age", "Age")),
        duration_minutes=_parse_first_int(_first_value(row, "duree_de_partie", "Durée de partie")),
        url=_first_value(row, "url", "Url") or None,
        image_url=_first_value(row, "url_image", "Url Image") or None,
        authors=_split_names(_first_value(row, "auteurs", "Auteurs"), (";", "/")),
        artists=_split_names(_first_value(row, "artistes", "Artistes"), (";", "/")),
        editors=_split_names(_first_value(row, "editeurs", "Editeurs"), (";", "/")),
        distributors=_split_names(_first_value(row, "distributeurs", "Distributeurs"), (";", "/")),
    )


def parse_args(argv=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Import games from a CSV file into SQLite.")
    parser.add_argument("--env-path", help="Path to the backend environment file.")
    parser.add_argument("--csv-path", default="data/raw/trictac_data.csv", help="Path to the CSV file.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum number of rows to import.")
    return parser.parse_args(argv)


def resolve_env_path(env_path: str | None) -> Path:
    """Resolve the environment file path."""
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate
        raise FileNotFoundError(f"Fichier d'environnement introuvable: {candidate}")

    for candidate in DEFAULT_ENV_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Fichier d'environnement introuvable")


def import_games(csv_path: str | Path, limit: int = 0) -> tuple[int, int]:
    """Import games from CSV into the SQLite-backed backend."""
    from . import crud
    from .database import init_db

    init_db()
    imported = 0
    skipped = 0
    with Path(csv_path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            if limit and index >= limit:
                break
            payload = build_game_payload(row)
            if payload is None:
                skipped += 1
                continue
            crud.create_game(payload)
            imported += 1
    return imported, skipped


def main(argv=None):
    """Run the CSV import script."""
    args = parse_args(argv)
    env_path = resolve_env_path(args.env_path)
    os.environ["ENV_PATH"] = str(env_path)
    return import_games(args.csv_path, args.limit)


if __name__ == "__main__":
    main()
