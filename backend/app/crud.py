"""CRUD helpers backed by SQLite."""

import sqlite3
from collections import defaultdict
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException

from . import schemas
from .database import get_connection


GAME_RELATIONS = {
    "authors": ("authors", "game_authors", "author_id"),
    "artists": ("artists", "game_artists", "artist_id"),
    "editors": ("editors", "game_editors", "editor_id"),
    "distributors": ("distributors", "game_distributors", "distributor_id"),
}


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convert a SQLite row to a plain dict."""
    return dict(row) if row is not None else None


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert SQLite rows to plain dicts."""
    return [dict(row) for row in rows]


def _raise_write_error(exc: sqlite3.IntegrityError, conflict_detail: str) -> None:
    """Map SQLite integrity errors to HTTP errors."""
    message = str(exc).lower()
    if "unique" in message:
        raise HTTPException(status_code=409, detail=conflict_detail) from exc
    if "foreign key" in message:
        raise HTTPException(status_code=400, detail="Referenced resource does not exist") from exc
    raise HTTPException(status_code=400, detail="Database write failed") from exc


def _fetch_paginated_rows(table: str, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
    """Fetch rows from a table using limit and offset."""
    if limit <= 0:
        return []
    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT * FROM {table} ORDER BY id LIMIT ? OFFSET ?",
            (limit, skip),
        ).fetchall()
    return _rows_to_dicts(rows)


def _build_game_filters(
    search: str | None = None,
    game_type: str | None = None,
    year: str | None = None,
) -> tuple[str, list[Any]]:
    """Build the SQL filter clause for paginated game queries."""
    clauses: list[str] = []
    parameters: list[Any] = []

    if search and search.strip():
        pattern = f"%{search.strip().lower()}%"
        clauses.append(
            """
            (
                LOWER(g.name) LIKE ?
                OR EXISTS (
                    SELECT 1
                    FROM game_authors ga
                    JOIN authors a ON a.id = ga.author_id
                    WHERE ga.game_id = g.id AND LOWER(a.name) LIKE ?
                )
                OR EXISTS (
                    SELECT 1
                    FROM game_editors ge
                    JOIN editors e ON e.id = ge.editor_id
                    WHERE ge.game_id = g.id AND LOWER(e.name) LIKE ?
                )
            )
            """
        )
        parameters.extend([pattern, pattern, pattern])

    if game_type and game_type.strip():
        clauses.append("LOWER(g.type) = ?")
        parameters.append(game_type.strip().lower())

    if year and year.strip():
        clauses.append("CAST(g.creation_year AS TEXT) LIKE ?")
        parameters.append(f"%{year.strip()}%")

    if not clauses:
        return "", parameters

    return f" WHERE {' AND '.join(clauses)}", parameters


def _fetch_row(table: str, row_id: Any) -> dict[str, Any] | None:
    """Fetch a single row by its primary key."""
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT * FROM {table} WHERE id = ?",
            (row_id,),
        ).fetchone()
    return _row_to_dict(row)


def _delete_row(table: str, row_id: Any) -> dict[str, Any] | None:
    """Delete a row by id and return the deleted payload when present."""
    row = _fetch_row(table, row_id)
    if row is None:
        return None
    with get_connection() as connection:
        connection.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
        connection.commit()
    return row


def _fetch_rows_by_ids(table: str, ids: list[Any]) -> list[dict[str, Any]]:
    """Fetch rows by a list of ids."""
    if not ids:
        return []
    placeholders = ", ".join("?" for _ in ids)
    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT * FROM {table} WHERE id IN ({placeholders})",
            tuple(ids),
        ).fetchall()
    return _rows_to_dicts(rows)


def _ensure_unique_names(names: list[str], entity_label: str) -> list[str]:
    """Validate and normalize related entity names."""
    cleaned_names = [name.strip() for name in names if name and name.strip()]
    if len(cleaned_names) != len(set(cleaned_names)):
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate {entity_label} names are not allowed",
        )
    return cleaned_names


def _get_or_create_named_entity(connection: sqlite3.Connection, table: str, name: str) -> dict[str, Any]:
    """Fetch a named row or create it when missing."""
    row = connection.execute(
        f"SELECT * FROM {table} WHERE name = ?",
        (name,),
    ).fetchone()
    if row is not None:
        return dict(row)

    try:
        cursor = connection.execute(
            f"INSERT INTO {table} (name) VALUES (?)",
            (name,),
        )
    except sqlite3.IntegrityError as exc:
        _raise_write_error(exc, f"{table[:-1].capitalize()} with this name already exists")
    return {"id": cursor.lastrowid, "name": name}


def _group_rows(rows: list[dict[str, Any]], key: str) -> dict[Any, list[dict[str, Any]]]:
    """Group rows by a foreign-key column."""
    grouped: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


def _load_game_relations(game_ids: list[int]) -> dict[str, dict[int, list[dict[str, Any]]]]:
    """Load authors, artists, editors and distributors for a set of games."""
    relations: dict[str, dict[int, list[dict[str, Any]]]] = {}
    if not game_ids:
        return relations

    placeholders = ", ".join("?" for _ in game_ids)
    with get_connection() as connection:
        for relation_name, (table, join_table, relation_id_column) in GAME_RELATIONS.items():
            join_rows = _rows_to_dicts(
                connection.execute(
                    f"SELECT game_id, {relation_id_column} FROM {join_table} "
                    f"WHERE game_id IN ({placeholders})",
                    tuple(game_ids),
                ).fetchall()
            )
            related_ids = sorted({row[relation_id_column] for row in join_rows})
            related_rows = _fetch_rows_by_ids(table, related_ids)
            related_by_id = {row["id"]: row for row in related_rows}

            grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
            for join_row in join_rows:
                related_row = related_by_id.get(join_row[relation_id_column])
                if related_row is not None:
                    grouped[join_row["game_id"]].append(related_row)
            relations[relation_name] = grouped

    return relations


def _serialize_game(game_row: dict[str, Any], relations: dict[str, dict[int, list[dict[str, Any]]]]) -> dict[str, Any]:
    """Convert a raw game row into the API response shape."""
    payload = dict(game_row)
    for relation_name in GAME_RELATIONS:
        payload[relation_name] = relations.get(relation_name, {}).get(game_row["id"], [])
    return payload


def _get_game_by_filters(**filters: Any) -> dict[str, Any] | None:
    """Fetch a single game using arbitrary equality filters."""
    where_clause = " AND ".join(f"{column} = ?" for column in filters)
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT * FROM games WHERE {where_clause} LIMIT 1",
            tuple(filters.values()),
        ).fetchone()
    if row is None:
        return None
    relations = _load_game_relations([row["id"]])
    return _serialize_game(dict(row), relations)


def _load_collection_relations(
    collection_ids: list[int],
    owner_ids: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[int, list[dict[str, Any]]], dict[int, list[dict[str, Any]]]]:
    """Load owners, shares and collection games for a set of collections."""
    owners = _fetch_rows_by_ids("users", owner_ids)
    owner_map = {str(owner["id"]): owner for owner in owners}
    if not collection_ids:
        return owner_map, {}, {}

    placeholders = ", ".join("?" for _ in collection_ids)
    with get_connection() as connection:
        shares = _rows_to_dicts(
            connection.execute(
                f"SELECT * FROM collection_shares WHERE collection_id IN ({placeholders})",
                tuple(collection_ids),
            ).fetchall()
        )
        games = _rows_to_dicts(
            connection.execute(
                f"SELECT * FROM collection_games WHERE collection_id IN ({placeholders})",
                tuple(collection_ids),
            ).fetchall()
        )
    return owner_map, _group_rows(shares, "collection_id"), _group_rows(games, "collection_id")


def _serialize_collection(
    collection_row: dict[str, Any],
    owner_map: dict[str, dict[str, Any]],
    shares_by_collection: dict[int, list[dict[str, Any]]],
    games_by_collection: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Convert a raw collection row into the API response shape."""
    collection_id = collection_row["id"]
    owner_id = str(collection_row["owner_id"])
    payload = dict(collection_row)
    payload["owner"] = owner_map.get(owner_id)
    payload["shares"] = shares_by_collection.get(collection_id, [])
    payload["games"] = games_by_collection.get(collection_id, [])
    return payload


def get_games(skip: int = 0, limit: int = 100):
    """Return paginated games with their related contributors."""
    game_rows = _fetch_paginated_rows("games", skip=skip, limit=limit)
    relations = _load_game_relations([row["id"] for row in game_rows])
    return [_serialize_game(row, relations) for row in game_rows]


def get_games_page(
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    game_type: str | None = None,
    year: str | None = None,
):
    """Return a paginated and filterable game page."""
    where_clause, parameters = _build_game_filters(search=search, game_type=game_type, year=year)

    with get_connection() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM games g{where_clause}",
            tuple(parameters),
        ).fetchone()[0]

        game_rows = _rows_to_dicts(
            connection.execute(
                f"SELECT * FROM games g{where_clause} ORDER BY g.id DESC LIMIT ? OFFSET ?",
                tuple([*parameters, limit, skip]),
            ).fetchall()
        )

    relations = _load_game_relations([row["id"] for row in game_rows])
    return {
        "items": [_serialize_game(row, relations) for row in game_rows],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


def get_game(game_id: int):
    """Return a single game by id."""
    return _get_game_by_filters(id=game_id)


def create_game(game: schemas.GameCreate):
    """Create a game and its contributor relations."""
    game_data = game.model_dump()
    related_names = {
        relation_name: _ensure_unique_names(game_data.pop(relation_name, []), relation_name[:-1])
        for relation_name in GAME_RELATIONS
    }

    with get_connection() as connection:
        columns = ", ".join(game_data.keys())
        placeholders = ", ".join("?" for _ in game_data)
        try:
            cursor = connection.execute(
                f"INSERT INTO games ({columns}) VALUES ({placeholders})",
                tuple(game_data.values()),
            )
            game_id = cursor.lastrowid
            for relation_name, names in related_names.items():
                table, join_table, relation_id_column = GAME_RELATIONS[relation_name]
                for name in names:
                    related_row = _get_or_create_named_entity(connection, table, name)
                    connection.execute(
                        f"INSERT INTO {join_table} (game_id, {relation_id_column}) VALUES (?, ?)",
                        (game_id, related_row["id"]),
                    )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            _raise_write_error(exc, "Game could not be created")

    return get_game(game_id)


def delete_game(game_id: int):
    """Delete a game and its join-table records."""
    return _delete_row("games", game_id)


def get_authors(skip: int = 0, limit: int = 100):
    """Return paginated authors."""
    return _fetch_paginated_rows("authors", skip=skip, limit=limit)


def get_author(author_id: int):
    """Return a single author."""
    return _fetch_row("authors", author_id)


def create_author(author: schemas.AuthorCreate):
    """Create an author."""
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO authors (name) VALUES (?)",
                (author.name,),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, "Author with this name already exists")
    return {"id": cursor.lastrowid, "name": author.name}


def delete_author(author_id: int):
    """Delete an author."""
    return _delete_row("authors", author_id)


def get_artists(skip: int = 0, limit: int = 100):
    """Return paginated artists."""
    return _fetch_paginated_rows("artists", skip=skip, limit=limit)


def get_artist(artist_id: int):
    """Return a single artist."""
    return _fetch_row("artists", artist_id)


def create_artist(artist: schemas.ArtistCreate):
    """Create an artist."""
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO artists (name) VALUES (?)",
                (artist.name,),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, "Artist with this name already exists")
    return {"id": cursor.lastrowid, "name": artist.name}


def delete_artist(artist_id: int):
    """Delete an artist."""
    return _delete_row("artists", artist_id)


def get_editors(skip: int = 0, limit: int = 100):
    """Return paginated editors."""
    return _fetch_paginated_rows("editors", skip=skip, limit=limit)


def get_editor(editor_id: int):
    """Return a single editor."""
    return _fetch_row("editors", editor_id)


def create_editor(editor: schemas.EditorCreate):
    """Create an editor."""
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO editors (name) VALUES (?)",
                (editor.name,),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, "Editor with this name already exists")
    return {"id": cursor.lastrowid, "name": editor.name}


def delete_editor(editor_id: int):
    """Delete an editor."""
    return _delete_row("editors", editor_id)


def get_distributors(skip: int = 0, limit: int = 100):
    """Return paginated distributors."""
    return _fetch_paginated_rows("distributors", skip=skip, limit=limit)


def get_distributor(distributor_id: int):
    """Return a single distributor."""
    return _fetch_row("distributors", distributor_id)


def create_distributor(distributor: schemas.DistributorCreate):
    """Create a distributor."""
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO distributors (name) VALUES (?)",
                (distributor.name,),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, "Distributor with this name already exists")
    return {"id": cursor.lastrowid, "name": distributor.name}


def delete_distributor(distributor_id: int):
    """Delete a distributor."""
    return _delete_row("distributors", distributor_id)


def get_users(skip: int = 0, limit: int = 100):
    """Return paginated users."""
    return _fetch_paginated_rows("users", skip=skip, limit=limit)


def get_user(user_id: str | UUID):
    """Return a single user."""
    return _fetch_row("users", str(user_id))


def create_user(user: schemas.UserCreate, user_id: UUID | None = None):
    """Create a user with an optional explicit id."""
    payload = user.model_dump()
    payload["id"] = str(user_id or uuid4())
    with get_connection() as connection:
        try:
            connection.execute(
                "INSERT INTO users (id, email, username) VALUES (?, ?, ?)",
                (payload["id"], payload["email"], payload["username"]),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, "User with this email already exists")
    return payload


def delete_user(user_id: str | UUID):
    """Delete a user."""
    return _delete_row("users", str(user_id))


def get_collections(skip: int = 0, limit: int = 100):
    """Return paginated collections with their owner, shares and games."""
    collections = _fetch_paginated_rows("collections", skip=skip, limit=limit)
    owner_ids = sorted({str(collection["owner_id"]) for collection in collections})
    owner_map, shares_by_collection, games_by_collection = _load_collection_relations(
        [collection["id"] for collection in collections],
        owner_ids,
    )
    return [
        _serialize_collection(collection, owner_map, shares_by_collection, games_by_collection)
        for collection in collections
    ]


def get_collection(collection_id: int):
    """Return a single collection by id."""
    collection = _fetch_row("collections", collection_id)
    if collection is None:
        return None

    owner_map, shares_by_collection, games_by_collection = _load_collection_relations(
        [collection_id],
        [str(collection["owner_id"])],
    )
    return _serialize_collection(collection, owner_map, shares_by_collection, games_by_collection)


def create_collection(collection: schemas.CollectionCreate):
    """Create a collection."""
    payload = collection.model_dump()
    payload["owner_id"] = str(payload["owner_id"])
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO collections (name, description, owner_id) VALUES (?, ?, ?)",
                (payload["name"], payload["description"], payload["owner_id"]),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, "Collection could not be created")
    return get_collection(cursor.lastrowid)


def delete_collection(collection_id: int):
    """Delete a collection and its dependent rows."""
    return _delete_row("collections", collection_id)


def get_collection_shares(skip: int = 0, limit: int = 100):
    """Return paginated collection shares."""
    return _fetch_paginated_rows("collection_shares", skip=skip, limit=limit)


def get_collection_share(share_id: int):
    """Return a single collection share."""
    return _fetch_row("collection_shares", share_id)


def create_collection_share(share: schemas.CollectionShareCreate, collection_id: int):
    """Create a collection share."""
    payload = share.model_dump()
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO collection_shares (collection_id, shared_with, permission) VALUES (?, ?, ?)",
                (collection_id, str(payload["shared_with"]), payload["permission"]),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, "Collection share already exists or is invalid")
    return {
        "id": cursor.lastrowid,
        "collection_id": collection_id,
        "shared_with": str(payload["shared_with"]),
        "permission": payload["permission"],
    }


def delete_collection_share(share_id: int):
    """Delete a collection share."""
    return _delete_row("collection_shares", share_id)


def get_user_locations(skip: int = 0, limit: int = 100):
    """Return paginated user locations."""
    return _fetch_paginated_rows("user_locations", skip=skip, limit=limit)


def get_user_location(location_id: int):
    """Return a single user location."""
    return _fetch_row("user_locations", location_id)


def create_user_location(location: schemas.UserLocationCreate):
    """Create a location for a user."""
    payload = location.model_dump()
    payload["user_id"] = str(payload["user_id"])
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                "INSERT INTO user_locations (user_id, name) VALUES (?, ?)",
                (payload["user_id"], payload["name"]),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, "User location already exists or is invalid")
    return {"id": cursor.lastrowid, **payload}


def delete_user_location(location_id: int):
    """Delete a user location."""
    return _delete_row("user_locations", location_id)


def get_collection_games(skip: int = 0, limit: int = 100):
    """Return paginated collection games."""
    return _fetch_paginated_rows("collection_games", skip=skip, limit=limit)


def get_collection_game(collection_game_id: int):
    """Return a single collection game."""
    return _fetch_row("collection_games", collection_game_id)


def create_collection_game(collection_game: schemas.CollectionGameCreate):
    """Create a collection game row."""
    payload = collection_game.model_dump()
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO collection_games (collection_id, game_id, location_id, quantity)
                VALUES (?, ?, ?, ?)
                """,
                (
                    payload["collection_id"],
                    payload["game_id"],
                    payload["location_id"],
                    payload["quantity"],
                ),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, "Collection game already exists or is invalid")
    return {"id": cursor.lastrowid, **payload}


def delete_collection_game(collection_game_id: int):
    """Delete a collection game."""
    return _delete_row("collection_games", collection_game_id)
