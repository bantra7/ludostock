"""Import Tric Trac game data into the Ludostock SQLite database."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sqlite3
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from backend.app.database import SCHEMA_STATEMENTS
from backend.app.schemas import GameCreate


LOGGER = logging.getLogger("import_data")
REQUEST_TIMEOUT = 20
DEFAULT_WORKERS = 8
CACHE_DEFAULT_PATH = Path("data/raw/trictac_enrichment_cache.json")
CSV_REQUIRED_COLUMNS = {
    "Url",
    "Nom",
    "Type",
    "Année de sortie",
    "Nombre de joueurs",
    "Age",
    "Durée de partie",
    "Url Image",
}
CONTRIBUTOR_COLUMNS = ("Auteurs", "Artistes", "Editeurs", "Distributeurs")
CONTRIBUTOR_LABELS = {
    "auteur": "Auteurs",
    "auteurs": "Auteurs",
    "auteurs_autrices": "Auteurs",
    "artiste": "Artistes",
    "artistes": "Artistes",
    "illustrateur": "Artistes",
    "illustrateurs": "Artistes",
    "editeur": "Editeurs",
    "editeurs": "Editeurs",
    "distributeur": "Distributeurs",
    "distributeurs": "Distributeurs",
}
RELATION_TABLES = {
    "authors": ("authors", "game_authors", "author_id"),
    "artists": ("artists", "game_artists", "artist_id"),
    "editors": ("editors", "game_editors", "editor_id"),
    "distributors": ("distributors", "game_distributors", "distributor_id"),
}
BASE_GAME_LABEL_KEYS = {
    "extension_de",
    "jeu_de_base",
    "jeu_parent",
    "base_game",
    "base_set",
    "game_system",
}
NULL_LIKE_VALUES = {"", "-", "nan", "none", "null", "nc", "n/a"}


@dataclass(slots=True)
class PreparedGame:
    """Represent a validated game ready for database insertion."""

    payload: GameCreate
    source_url: str
    base_game_url: str | None = None
    base_game_name: str | None = None
    database_id: int | None = None


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Importe data/raw/trictac_data_games.csv dans une base SQLite Ludostock en "
            "reconstruisant les relations auteurs/artistes/editeurs/distributeurs."
        )
    )
    parser.add_argument(
        "--csv-path",
        default="data/raw/trictac_data_games.csv",
        help="Chemin vers le CSV Tric Trac source.",
    )
    parser.add_argument(
        "--db-path",
        default="ludostock.db",
        help="Chemin de sortie du fichier SQLite.",
    )
    parser.add_argument(
        "--cache-path",
        default=str(CACHE_DEFAULT_PATH),
        help="Chemin du cache JSON des enrichissements web.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="Nombre de workers utilises pour l'enrichissement web.",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=REQUEST_TIMEOUT,
        help="Timeout HTTP par requete, en secondes.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Supprime le fichier .db cible avant l'import.",
    )
    parser.add_argument(
        "--enrich-missing-contributors",
        action="store_true",
        help="Recupere auteurs/artistes/editeurs/distributeurs depuis les URLs Tric Trac.",
    )
    parser.add_argument(
        "--allow-missing-relations",
        action="store_true",
        help="Autorise l'import meme si certains contributeurs restent introuvables.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Niveau de log du script.",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    """Configure the script logger."""
    logging.basicConfig(level=getattr(logging, level), format="%(levelname)s %(message)s")


def load_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    """Load CSV rows with a small encoding fallback list."""
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    last_error: UnicodeDecodeError | None = None
    for encoding in encodings:
        try:
            with csv_path.open("r", encoding=encoding, newline="") as file_handle:
                reader = csv.DictReader(file_handle)
                rows = list(reader)
            LOGGER.info("CSV charge depuis %s avec l'encodage %s", csv_path, encoding)
            return rows
        except UnicodeDecodeError as exc:
            last_error = exc

    raise RuntimeError(f"Impossible de lire {csv_path} avec les encodages testes") from last_error


def validate_csv_columns(rows: list[dict[str, str]]) -> None:
    """Ensure the CSV contains the minimum expected structure."""
    if not rows:
        raise ValueError("Le CSV ne contient aucune ligne.")

    available_columns = set(rows[0].keys())
    missing_columns = sorted(CSV_REQUIRED_COLUMNS - available_columns)
    if missing_columns:
        raise ValueError(
            "Le CSV ne contient pas toutes les colonnes attendues : "
            + ", ".join(missing_columns)
        )


def normalize_label(value: str) -> str:
    """Normalize a label to a stable ASCII key."""
    normalized = unicodedata.normalize("NFKD", value)
    stripped = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", "_", stripped.lower()).strip("_")


def normalize_name_key(value: str | None) -> str:
    """Normalize a game name to a fuzzy matching key."""
    if not value:
        return ""
    lowered = value.casefold().replace("&", " et ")
    normalized = unicodedata.normalize("NFKD", lowered)
    stripped = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", stripped).strip()


def clean_text(value: Any) -> str | None:
    """Return a stripped string or None for null-like values."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.casefold() in NULL_LIKE_VALUES:
        return None
    return text


def normalize_game_type(value: str | None) -> str:
    """Normalize Tric Trac game types to backend values."""
    text = clean_text(value)
    if text is None:
        return "jeu"
    return "extension" if "extension" in text.casefold() else "jeu"


def parse_year(value: str | None) -> int | None:
    """Extract a four-digit year from a text field."""
    text = clean_text(value)
    if text is None:
        return None
    match = re.search(r"(19|20)\d{2}", text)
    return int(match.group(0)) if match else None


def parse_player_range(value: str | None) -> tuple[int | None, int | None]:
    """Parse the minimum and maximum player counts."""
    text = clean_text(value)
    if text is None:
        return None, None
    numbers = [int(match) for match in re.findall(r"\d+", text)]
    if not numbers:
        return None, None
    if len(numbers) == 1:
        return numbers[0], numbers[0]
    return min(numbers), max(numbers)


def parse_age(value: str | None) -> int | None:
    """Extract the minimum recommended age."""
    text = clean_text(value)
    if text is None:
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def parse_duration(value: str | None) -> int | None:
    """Extract the duration in minutes."""
    text = clean_text(value)
    if text is None:
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def split_contributors(value: str | None) -> list[str]:
    """Split contributor names from a CSV or scraped text field."""
    text = clean_text(value)
    if text is None:
        return []
    parts = re.split(r"\s*/\s*|\s*;\s*|\s*\|\s*", text)
    deduplicated: list[str] = []
    seen: set[str] = set()
    for part in parts:
        cleaned = clean_text(part)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            deduplicated.append(cleaned)
    return deduplicated


def extract_text(element: BeautifulSoup | None) -> str | None:
    """Extract clean text from a BeautifulSoup element."""
    if element is None:
        return None
    text = element.get_text(" ", strip=True)
    return clean_text(text)


def resolve_image_url(src: str | None) -> str | None:
    """Resolve the underlying image URL from Tric Trac image wrappers."""
    text = clean_text(src)
    if text is None:
        return None
    parsed_url = urlparse(text)
    params = parse_qs(parsed_url.query)
    return unquote(params.get("url", [""])[0]) or text


def load_enrichment_cache(cache_path: Path) -> dict[str, dict[str, Any]]:
    """Load the JSON cache that stores per-URL enrichments."""
    if not cache_path.exists():
        return {}
    with cache_path.open("r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)
    if not isinstance(data, dict):
        raise ValueError(f"Le cache {cache_path} doit contenir un objet JSON.")
    return data


def save_enrichment_cache(cache_path: Path, cache: dict[str, dict[str, Any]]) -> None:
    """Persist the enrichment cache."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("w", encoding="utf-8") as file_handle:
        json.dump(cache, file_handle, ensure_ascii=False, indent=2, sort_keys=True)


def fetch_game_enrichment(url: str, timeout: int = REQUEST_TIMEOUT) -> dict[str, Any]:
    """Fetch missing contributor and relation data from a Tric Trac game page."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
        )
    }
    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()

    if "login-silent" in response.url:
        raise RuntimeError(
            "Tric Trac redirige vers une page de reconnexion silencieuse, "
            "les donnees detaillees ne sont pas accessibles."
        )

    soup = BeautifulSoup(response.text, "html.parser")
    enrichment: dict[str, Any] = {column: [] for column in CONTRIBUTOR_COLUMNS}
    enrichment["base_game_name"] = None
    enrichment["base_game_url"] = None

    contributor_blocks = soup.select("span.style_conceptorsSpecs___QBek[title]")
    for contributor_block in contributor_blocks:
        title = clean_text(contributor_block.get("title"))
        if not title:
            continue
        names = [
            anchor.get_text(strip=True)
            for anchor in contributor_block.select("a")
            if clean_text(anchor.get_text(strip=True))
        ]
        if not names:
            continue
        label = CONTRIBUTOR_LABELS.get(normalize_label(title))
        if label:
            enrichment[label] = names

    table = soup.select_one("table.style_specsItems__HUu7f")
    if table:
        for row in table.select("tr"):
            label = extract_text(row.select_one("th"))
            if not label:
                continue
            normalized_key = normalize_label(label)
            if normalized_key not in BASE_GAME_LABEL_KEYS:
                continue
            value_cell = row.select_one("td")
            enrichment["base_game_name"] = extract_text(value_cell)
            link = value_cell.select_one("a[href]") if value_cell else None
            if link is not None:
                enrichment["base_game_url"] = urljoin(url, link["href"])
            break

    image = soup.select_one("img[itemprop='image']")
    image_url = resolve_image_url(image.get("src") if image else None)
    if image_url:
        enrichment["image_url"] = image_url

    return enrichment


def needs_contributor_enrichment(row: dict[str, str]) -> bool:
    """Return True when the row does not already include contributor data."""
    return not any(split_contributors(row.get(column)) for column in CONTRIBUTOR_COLUMNS)


def enrich_rows(
    rows: list[dict[str, str]],
    cache_path: Path,
    workers: int,
    timeout: int,
) -> dict[str, dict[str, Any]]:
    """Enrich rows by fetching missing data from Tric Trac pages."""
    cache = load_enrichment_cache(cache_path)
    urls_to_fetch = [
        row["Url"]
        for row in rows
        if clean_text(row.get("Url")) and needs_contributor_enrichment(row) and row["Url"] not in cache
    ]
    if not urls_to_fetch:
        LOGGER.info("Aucun enrichissement distant supplementaire n'est necessaire.")
        return cache

    LOGGER.info("Enrichissement de %s fiches Tric Trac...", len(urls_to_fetch))
    completed = 0
    failures = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_to_url = {
            executor.submit(fetch_game_enrichment, url, timeout): url for url in urls_to_fetch
        }
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            completed += 1
            try:
                cache[url] = future.result()
            except Exception as exc:  # noqa: BLE001
                failures += 1
                LOGGER.warning("Echec de l'enrichissement pour %s: %s", url, exc)
            if completed % 100 == 0 or completed == len(urls_to_fetch):
                LOGGER.info(
                    "Enrichissement: %s/%s traitees (%s echecs)",
                    completed,
                    len(urls_to_fetch),
                    failures,
                )
                save_enrichment_cache(cache_path, cache)

    save_enrichment_cache(cache_path, cache)
    return cache


def row_to_game_payload(row: dict[str, str], enrichment: dict[str, Any] | None) -> PreparedGame:
    """Convert a CSV row plus optional enrichment data into a validated GameCreate payload."""
    contributors = {
        "authors": split_contributors(row.get("Auteurs")),
        "artists": split_contributors(row.get("Artistes")),
        "editors": split_contributors(row.get("Editeurs")),
        "distributors": split_contributors(row.get("Distributeurs")),
    }
    if enrichment:
        contributors["authors"] = contributors["authors"] or list(enrichment.get("Auteurs", []))
        contributors["artists"] = contributors["artists"] or list(enrichment.get("Artistes", []))
        contributors["editors"] = contributors["editors"] or list(enrichment.get("Editeurs", []))
        contributors["distributors"] = contributors["distributors"] or list(
            enrichment.get("Distributeurs", [])
        )

    min_players, max_players = parse_player_range(row.get("Nombre de joueurs"))
    payload = GameCreate(
        name=clean_text(row.get("Nom")) or "Sans nom",
        type=normalize_game_type(row.get("Type")),
        creation_year=parse_year(row.get("Année de sortie")),
        min_players=min_players,
        max_players=max_players,
        min_age=parse_age(row.get("Age")),
        duration_minutes=parse_duration(row.get("Durée de partie")),
        url=clean_text(row.get("Url")),
        image_url=clean_text(row.get("Url Image")) or clean_text(enrichment.get("image_url") if enrichment else None),
        authors=contributors["authors"],
        artists=contributors["artists"],
        editors=contributors["editors"],
        distributors=contributors["distributors"],
    )

    return PreparedGame(
        payload=payload,
        source_url=payload.url or "",
        base_game_url=clean_text(enrichment.get("base_game_url") if enrichment else None),
        base_game_name=clean_text(enrichment.get("base_game_name") if enrichment else None),
    )


def prepare_games(
    rows: list[dict[str, str]],
    enrichments: dict[str, dict[str, Any]],
    allow_missing_relations: bool,
) -> list[PreparedGame]:
    """Build validated game payloads from CSV rows."""
    prepared_games: list[PreparedGame] = []
    missing_relations = 0

    for row in rows:
        enrichment = enrichments.get(row.get("Url", "")) if row.get("Url") else None
        prepared_game = row_to_game_payload(row, enrichment)
        prepared_games.append(prepared_game)

        if not (
            prepared_game.payload.authors
            or prepared_game.payload.artists
            or prepared_game.payload.editors
            or prepared_game.payload.distributors
        ):
            missing_relations += 1

    if missing_relations and not allow_missing_relations:
        raise ValueError(
            f"{missing_relations} jeux n'ont aucun contributeur exploitable. "
            "Relancez avec --enrich-missing-contributors ou, en dernier recours, "
            "--allow-missing-relations."
        )

    LOGGER.info(
        "%s jeux prepares (%s sans contributeur complet).",
        len(prepared_games),
        missing_relations,
    )
    return prepared_games


def recreate_database(db_path: Path, force: bool) -> sqlite3.Connection:
    """Create a fresh SQLite database initialized with the backend schema."""
    if db_path.exists():
        if not force:
            raise FileExistsError(
                f"Le fichier {db_path} existe deja. Utilisez --force pour l'ecraser."
            )
        db_path.unlink()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    for statement in SCHEMA_STATEMENTS:
        connection.execute(statement)
    connection.commit()
    return connection


def get_or_create_named_entity(
    connection: sqlite3.Connection,
    table: str,
    cache: dict[str, int],
    name: str,
) -> int:
    """Insert a contributor once and return its identifier."""
    if name in cache:
        return cache[name]

    cursor = connection.execute(f"INSERT OR IGNORE INTO {table} (name) VALUES (?)", (name,))
    entity_id = cursor.lastrowid
    if not entity_id:
        entity_id = connection.execute(
            f"SELECT id FROM {table} WHERE name = ?",
            (name,),
        ).fetchone()["id"]
    cache[name] = entity_id
    return entity_id


def insert_games(connection: sqlite3.Connection, games: list[PreparedGame]) -> None:
    """Insert games and join-table relations into SQLite."""
    entity_caches = {table: {} for table, _, _ in RELATION_TABLES.values()}

    with connection:
        for index, prepared_game in enumerate(games, start=1):
            payload = prepared_game.payload
            cursor = connection.execute(
                """
                INSERT INTO games (
                    name,
                    type,
                    extension_of_id,
                    creation_year,
                    min_players,
                    max_players,
                    min_age,
                    duration_minutes,
                    url,
                    image_url
                )
                VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.name,
                    payload.type,
                    payload.creation_year,
                    payload.min_players,
                    payload.max_players,
                    payload.min_age,
                    payload.duration_minutes,
                    payload.url,
                    payload.image_url,
                ),
            )
            prepared_game.database_id = cursor.lastrowid

            for relation_name, names in (
                ("authors", payload.authors),
                ("artists", payload.artists),
                ("editors", payload.editors),
                ("distributors", payload.distributors),
            ):
                table, join_table, relation_column = RELATION_TABLES[relation_name]
                entity_cache = entity_caches[table]
                for name in names:
                    related_id = get_or_create_named_entity(connection, table, entity_cache, name)
                    connection.execute(
                        f"""
                        INSERT OR IGNORE INTO {join_table} (game_id, {relation_column})
                        VALUES (?, ?)
                        """,
                        (prepared_game.database_id, related_id),
                    )

            if index % 1000 == 0 or index == len(games):
                LOGGER.info("Insertion SQLite: %s/%s jeux", index, len(games))


def infer_base_name_candidates(game_name: str) -> list[str]:
    """Infer possible base-game names for an extension."""
    candidates: list[str] = []
    cleaned_name = game_name.strip()

    if ":" in cleaned_name:
        candidates.append(cleaned_name.split(":", maxsplit=1)[0].strip())
    if " - " in cleaned_name:
        candidates.append(cleaned_name.split(" - ", maxsplit=1)[0].strip())

    keyword_patterns = (
        r"\bextension\b.*$",
        r"\bmini-extension\b.*$",
        r"\bmicro extension\b.*$",
        r"\bcharacter pack\b.*$",
        r"\bpromo\b.*$",
        r"\bpack\b.*$",
        r"\bcampagne\b.*$",
    )
    for pattern in keyword_patterns:
        reduced = re.sub(pattern, "", cleaned_name, flags=re.IGNORECASE).strip(" :-")
        if reduced and reduced != cleaned_name:
            candidates.append(reduced)

    deduplicated: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = normalize_name_key(candidate)
        if key and key not in seen:
            seen.add(key)
            deduplicated.append(candidate)
    return deduplicated


def build_game_lookup(games: list[PreparedGame]) -> tuple[dict[str, int], dict[str, list[PreparedGame]]]:
    """Build URL and name indexes for post-processing relations."""
    by_url = {
        game.source_url: game.database_id
        for game in games
        if game.source_url and game.database_id is not None
    }
    by_name: dict[str, list[PreparedGame]] = {}
    for game in games:
        key = normalize_name_key(game.payload.name)
        if key:
            by_name.setdefault(key, []).append(game)
    return by_url, by_name


def choose_base_game(
    extension_game: PreparedGame,
    by_url: dict[str, int],
    by_name: dict[str, list[PreparedGame]],
) -> int | None:
    """Choose the most plausible base game identifier for an extension."""
    if extension_game.base_game_url:
        base_id = by_url.get(extension_game.base_game_url)
        if base_id and base_id != extension_game.database_id:
            return base_id

    candidate_names: list[str] = []
    if extension_game.base_game_name:
        candidate_names.append(extension_game.base_game_name)
    candidate_names.extend(infer_base_name_candidates(extension_game.payload.name))

    for candidate_name in candidate_names:
        candidates = [
            game
            for game in by_name.get(normalize_name_key(candidate_name), [])
            if game.database_id is not None and game.database_id != extension_game.database_id
        ]
        preferred_candidates = [game for game in candidates if game.payload.type == "jeu"]
        if len(preferred_candidates) == 1:
            return preferred_candidates[0].database_id
        if len(candidates) == 1:
            return candidates[0].database_id

    return None


def link_extensions(connection: sqlite3.Connection, games: list[PreparedGame]) -> int:
    """Populate extension_of_id for extensions that can be matched reliably."""
    by_url, by_name = build_game_lookup(games)
    linked_extensions = 0

    with connection:
        for game in games:
            if game.payload.type != "extension" or game.database_id is None:
                continue
            base_id = choose_base_game(game, by_url, by_name)
            if base_id is None:
                continue
            connection.execute(
                "UPDATE games SET extension_of_id = ? WHERE id = ?",
                (base_id, game.database_id),
            )
            linked_extensions += 1

    LOGGER.info("%s extensions reliees a un jeu parent.", linked_extensions)
    return linked_extensions


def summarize_database(connection: sqlite3.Connection) -> dict[str, int]:
    """Return a compact row-count summary for key tables."""
    tables = (
        "games",
        "authors",
        "artists",
        "editors",
        "distributors",
        "game_authors",
        "game_artists",
        "game_editors",
        "game_distributors",
    )
    return {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables
    }


def main() -> None:
    """Run the end-to-end CSV to SQLite import."""
    args = parse_arguments()
    configure_logging(args.log_level)

    csv_path = Path(args.csv_path)
    db_path = Path(args.db_path)
    cache_path = Path(args.cache_path)

    rows = load_csv_rows(csv_path)
    validate_csv_columns(rows)

    enrichments: dict[str, dict[str, Any]] = {}
    if args.enrich_missing_contributors:
        enrichments = enrich_rows(
            rows=rows,
            cache_path=cache_path,
            workers=args.workers,
            timeout=args.request_timeout,
        )

    games = prepare_games(
        rows=rows,
        enrichments=enrichments,
        allow_missing_relations=args.allow_missing_relations,
    )

    connection = recreate_database(db_path, force=args.force)
    try:
        insert_games(connection, games)
        link_extensions(connection, games)
        summary = summarize_database(connection)
    finally:
        connection.close()

    LOGGER.info("Import termine vers %s", db_path)
    for table, row_count in summary.items():
        LOGGER.info("%s: %s", table, row_count)


if __name__ == "__main__":
    main()
