"""CRUD helpers backed by SQLite."""

import logging
import os
import secrets
import sqlite3
from collections import defaultdict
from typing import Any, Literal
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

GameSortField = Literal["name", "type", "creation_year", "players", "duration_minutes", "authors", "editors"]
GameSortDirection = Literal["asc", "desc"]
SHARE_PERMISSION_VIEWER = "viewer"
logger = logging.getLogger("ludostock.backend.collection")


def _runtime_log_context() -> dict[str, str]:
    """Return runtime identifiers that help correlate backend collection logs."""
    return {
        "hostname": os.environ.get("HOSTNAME", "unknown"),
        "service": os.environ.get("K_SERVICE", "unknown"),
        "revision": os.environ.get("K_REVISION", "unknown"),
        "sqlite_path": os.environ.get("SQLITE_PATH", ""),
        "sqlite_seed_path": os.environ.get("SQLITE_SEED_PATH", ""),
    }


def _auth_user_log_context(auth_user: dict[str, Any]) -> dict[str, str]:
    """Return a compact, log-friendly representation of the authenticated user."""
    return {
        "email": str(auth_user.get("email") or "").strip().lower() or "-",
        "name": str(auth_user.get("name") or "").strip() or "-",
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


def _fetch_row_by_column(table: str, column: str, value: Any) -> dict[str, Any] | None:
    """Fetch a single row from a table using an equality filter."""
    with get_connection() as connection:
        row = connection.execute(
            f"SELECT * FROM {table} WHERE {column} = ? LIMIT 1",
            (value,),
        ).fetchone()
    return _row_to_dict(row)


def _build_game_filters(
    search: str | None = None,
    game_type: str | None = None,
    year: str | None = None,
) -> tuple[str, list[Any]]:
    """Build the SQL filter clause for paginated game queries."""
    clauses, parameters = _build_game_filter_clauses(search=search, game_type=game_type, year=year)

    if not clauses:
        return "", parameters

    return f" WHERE {' AND '.join(clauses)}", parameters


def _build_game_filter_clauses(
    search: str | None = None,
    game_type: str | None = None,
    year: str | None = None,
    table_alias: str = "g",
) -> tuple[list[str], list[Any]]:
    """Build SQL filter clauses and parameters for game queries."""
    clauses: list[str] = []
    parameters: list[Any] = []

    if search and search.strip():
        pattern = f"%{search.strip().lower()}%"
        clauses.append(f"LOWER({table_alias}.name) LIKE ?")
        parameters.append(pattern)

    if game_type and game_type.strip():
        clauses.append(f"LOWER({table_alias}.type) = ?")
        parameters.append(game_type.strip().lower())

    if year and year.strip():
        clauses.append(f"CAST({table_alias}.creation_year AS TEXT) LIKE ?")
        parameters.append(f"%{year.strip()}%")

    return clauses, parameters


def _build_game_order(sort_by: GameSortField = "name", sort_dir: GameSortDirection = "asc") -> str:
    """Build a safe SQL ORDER BY clause for game pages."""
    direction = "DESC" if sort_dir == "desc" else "ASC"
    author_sort = (
        "COALESCE(("
        "SELECT MIN(LOWER(a.name)) "
        "FROM game_authors ga "
        "JOIN authors a ON a.id = ga.author_id "
        "WHERE ga.game_id = g.id"
        "), '')"
    )
    editor_sort = (
        "COALESCE(("
        "SELECT MIN(LOWER(e.name)) "
        "FROM game_editors ge "
        "JOIN editors e ON e.id = ge.editor_id "
        "WHERE ge.game_id = g.id"
        "), '')"
    )

    if sort_by == "name":
        return f"LOWER(g.name) {direction}, g.id DESC"

    if sort_by == "type":
        return f"LOWER(g.type) {direction}, LOWER(g.name) ASC, g.id DESC"

    if sort_by == "creation_year":
        return f"(g.creation_year IS NULL) ASC, g.creation_year {direction}, LOWER(g.name) ASC, g.id DESC"

    if sort_by == "players":
        return (
            f"(g.min_players IS NULL) ASC, g.min_players {direction}, "
            f"(g.max_players IS NULL) ASC, g.max_players {direction}, LOWER(g.name) ASC, g.id DESC"
        )

    if sort_by == "duration_minutes":
        return f"(g.duration_minutes IS NULL) ASC, g.duration_minutes {direction}, LOWER(g.name) ASC, g.id DESC"

    if sort_by == "authors":
        return f"{author_sort} {direction}, LOWER(g.name) ASC, g.id DESC"

    return f"{editor_sort} {direction}, LOWER(g.name) ASC, g.id DESC"


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


def _update_named_row(table: str, row_id: Any, name: str, duplicate_message: str) -> dict[str, Any] | None:
    """Update a named row and return the updated payload when present."""
    if _fetch_row(table, row_id) is None:
        return None

    with get_connection() as connection:
        try:
            connection.execute(
                f"UPDATE {table} SET name = ? WHERE id = ?",
                (name, row_id),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            _raise_write_error(exc, duplicate_message)
    return _fetch_row(table, row_id)


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
    payload["share_enabled"] = bool(payload.get("share_enabled"))
    payload["owner"] = owner_map.get(owner_id)
    payload["shares"] = shares_by_collection.get(collection_id, [])
    payload["games"] = games_by_collection.get(collection_id, [])
    return payload


def _get_authenticated_user_profile(auth_user: dict[str, Any]) -> dict[str, str]:
    """Extract the unique name and email of the authenticated user."""
    username = str(auth_user.get("name") or "").strip()
    email = str(auth_user.get("email") or "").strip().lower()

    if not username:
        raise HTTPException(status_code=400, detail="Authenticated user name is required")
    if not email:
        raise HTTPException(status_code=400, detail="Authenticated user email is required")

    return {"username": username, "email": email}


def _sync_user_profile(user_id: str, email: str, username: str) -> dict[str, Any]:
    """Update the stored profile for an existing user."""
    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET email = ?, username = ? WHERE id = ?",
            (email, username, user_id),
        )
        connection.commit()
    return get_user(user_id)


def _get_or_create_authenticated_user(auth_user: dict[str, Any]) -> dict[str, Any]:
    """Return the local user row matching the authenticated Google profile."""
    profile = _get_authenticated_user_profile(auth_user)
    existing_user = get_user_by_username(profile["username"]) or get_user_by_email(profile["email"])
    runtime = _runtime_log_context()

    if existing_user is None:
        created_user = create_user(
            schemas.UserCreate(email=profile["email"], username=profile["username"]),
        )
        logger.info(
            "auth.user_created email=%s username=%s user_id=%s service=%s revision=%s hostname=%s sqlite_path=%s",
            profile["email"],
            profile["username"],
            created_user["id"],
            runtime["service"],
            runtime["revision"],
            runtime["hostname"],
            runtime["sqlite_path"] or "-",
        )
        return created_user

    needs_sync = (
        str(existing_user.get("email") or "").strip().lower() != profile["email"]
        or str(existing_user.get("username") or "").strip() != profile["username"]
    )
    if needs_sync:
        synced_user = _sync_user_profile(existing_user["id"], profile["email"], profile["username"])
        logger.info(
            "auth.user_synced email=%s username=%s user_id=%s service=%s revision=%s hostname=%s sqlite_path=%s",
            profile["email"],
            profile["username"],
            synced_user["id"],
            runtime["service"],
            runtime["revision"],
            runtime["hostname"],
            runtime["sqlite_path"] or "-",
        )
        return synced_user

    return existing_user


def _get_collection_by_owner(owner_id: str | UUID) -> dict[str, Any] | None:
    """Fetch the first collection owned by a given user."""
    return _fetch_row_by_column("collections", "owner_id", str(owner_id))


def _get_or_create_personal_collection(auth_user: dict[str, Any]) -> dict[str, Any]:
    """Return the authenticated user's personal collection, creating it when missing."""
    user = _get_or_create_authenticated_user(auth_user)
    collection = _get_collection_by_owner(user["id"])
    runtime = _runtime_log_context()

    if collection is None:
        username = str(user.get("username") or "").strip() or "Utilisateur"
        collection = create_collection(
            schemas.CollectionCreate(
                name=f"Collection de {username}",
                description=f"Collection personnelle de {username}",
                owner_id=UUID(str(user["id"])),
            )
        )
        logger.info(
            "collection.created owner_user_id=%s owner_email=%s collection_id=%s service=%s revision=%s hostname=%s sqlite_path=%s",
            user["id"],
            str(user.get("email") or "").strip().lower() or "-",
            collection["id"],
            runtime["service"],
            runtime["revision"],
            runtime["hostname"],
            runtime["sqlite_path"] or "-",
        )

    return collection


def _create_share_token() -> str:
    """Return a URL-safe token used in collection share links."""
    return secrets.token_urlsafe(24)


def _get_collection_share_by_user(collection_id: int, user_id: str | UUID) -> dict[str, Any] | None:
    """Return the share row granting a user access to a collection."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM collection_shares
            WHERE collection_id = ? AND shared_with = ?
            LIMIT 1
            """,
            (collection_id, str(user_id)),
        ).fetchone()
    return _row_to_dict(row)


def _get_collection_by_share_token(share_token: str) -> dict[str, Any] | None:
    """Return an enabled collection matching a share token."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM collections
            WHERE share_token = ? AND share_enabled = 1
            LIMIT 1
            """,
            (share_token,),
        ).fetchone()
    return _row_to_dict(row)


def _list_collection_subscribers(collection_id: int) -> list[dict[str, Any]]:
    """Return the subscribers that can view a collection."""
    with get_connection() as connection:
        rows = _rows_to_dicts(
            connection.execute(
                """
                SELECT
                    cs.id,
                    cs.collection_id,
                    cs.shared_with,
                    cs.permission,
                    u.id AS user_id,
                    u.email AS user_email,
                    u.username AS user_username
                FROM collection_shares cs
                JOIN users u ON u.id = cs.shared_with
                WHERE cs.collection_id = ?
                ORDER BY LOWER(COALESCE(u.username, u.email)) ASC, cs.id ASC
                """,
                (collection_id,),
            ).fetchall()
        )

    return [
        {
            "id": row["id"],
            "collection_id": row["collection_id"],
            "shared_with": row["shared_with"],
            "permission": row["permission"],
            "user": {
                "id": row["user_id"],
                "email": row["user_email"],
                "username": row["user_username"],
            },
        }
        for row in rows
    ]


def _build_collection_board_payload(collection: dict[str, Any], owner: dict[str, Any]) -> dict[str, Any]:
    """Return collection locations and game rows grouped for board views."""
    with get_connection() as connection:
        location_rows = _rows_to_dicts(
            connection.execute(
                """
                SELECT *
                FROM user_locations
                WHERE user_id = ?
                ORDER BY LOWER(name) ASC, id ASC
                """,
                (str(owner["id"]),),
            ).fetchall()
        )
        collection_game_rows = _rows_to_dicts(
            connection.execute(
                """
                SELECT *
                FROM collection_games
                WHERE collection_id = ?
                ORDER BY id ASC
                """,
                (collection["id"],),
            ).fetchall()
        )

    game_ids = [row["game_id"] for row in collection_game_rows]
    game_rows = _fetch_rows_by_ids("games", game_ids)
    relations = _load_game_relations([row["id"] for row in game_rows])
    games_by_id = {row["id"]: _serialize_game(row, relations) for row in game_rows}

    items = [
        {
            **row,
            "game": games_by_id[row["game_id"]],
        }
        for row in collection_game_rows
        if row["game_id"] in games_by_id
    ]

    return {
        "locations": location_rows,
        "items": items,
    }


def _serialize_shared_collection_summary(share_row: dict[str, Any], collection_row: dict[str, Any], owner: dict[str, Any]) -> dict[str, Any]:
    """Return a compact payload describing a collection shared with the current user."""
    with get_connection() as connection:
        game_count = connection.execute(
            "SELECT COUNT(*) FROM collection_games WHERE collection_id = ?",
            (collection_row["id"],),
        ).fetchone()[0]

    return {
        "collection_id": collection_row["id"],
        "share_id": share_row["id"],
        "permission": share_row["permission"],
        "name": collection_row["name"],
        "description": collection_row["description"],
        "owner": owner,
        "game_count": game_count,
    }


def _get_collection_game_by_identity(
    collection_id: int,
    game_id: int,
    location_id: int | None = None,
) -> dict[str, Any] | None:
    """Fetch a collection game row by its natural key."""
    with get_connection() as connection:
        if location_id is None:
            row = connection.execute(
                """
                SELECT *
                FROM collection_games
                WHERE collection_id = ? AND game_id = ? AND location_id IS NULL
                LIMIT 1
                """,
                (collection_id, game_id),
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT *
                FROM collection_games
                WHERE collection_id = ? AND game_id = ? AND location_id = ?
                LIMIT 1
                """,
                (collection_id, game_id, location_id),
            ).fetchone()
    return _row_to_dict(row)


def _get_collection_game_by_game_id(collection_id: int, game_id: int) -> dict[str, Any] | None:
    """Fetch the first collection game matching a collection and game id."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM collection_games
            WHERE collection_id = ? AND game_id = ?
            LIMIT 1
            """,
            (collection_id, game_id),
        ).fetchone()
    return _row_to_dict(row)


def _get_user_location_for_user(user_id: str, location_id: int) -> dict[str, Any] | None:
    """Return a location only when it belongs to the given user."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM user_locations
            WHERE id = ? AND user_id = ?
            LIMIT 1
            """,
            (location_id, user_id),
        ).fetchone()
    return _row_to_dict(row)


def _require_personal_location(user_id: str, location_id: int | None) -> None:
    """Validate that an optional location belongs to the authenticated user."""
    if location_id is None:
        return

    if _get_user_location_for_user(user_id, location_id) is None:
        raise HTTPException(status_code=404, detail="User location not found")


def _count_collection_games(connection: sqlite3.Connection, collection_id: int) -> int:
    """Return how many collection game rows exist for a collection."""
    row = connection.execute(
        "SELECT COUNT(*) AS total FROM collection_games WHERE collection_id = ?",
        (collection_id,),
    ).fetchone()
    return int(row["total"] if row is not None else 0)


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
    sort_by: GameSortField = "name",
    sort_dir: GameSortDirection = "asc",
):
    """Return a paginated and filterable game page."""
    where_clause, parameters = _build_game_filters(search=search, game_type=game_type, year=year)
    order_clause = _build_game_order(sort_by=sort_by, sort_dir=sort_dir)

    with get_connection() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) FROM games g{where_clause}",
            tuple(parameters),
        ).fetchone()[0]

        game_rows = _rows_to_dicts(
            connection.execute(
                f"SELECT * FROM games g{where_clause} ORDER BY {order_clause} LIMIT ? OFFSET ?",
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


def update_author(author_id: int, author: schemas.AuthorUpdate):
    """Update an author."""
    return _update_named_row("authors", author_id, author.name, "Author with this name already exists")


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


def update_artist(artist_id: int, artist: schemas.ArtistUpdate):
    """Update an artist."""
    return _update_named_row("artists", artist_id, artist.name, "Artist with this name already exists")


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


def update_editor(editor_id: int, editor: schemas.EditorUpdate):
    """Update an editor."""
    return _update_named_row("editors", editor_id, editor.name, "Editor with this name already exists")


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


def update_distributor(distributor_id: int, distributor: schemas.DistributorUpdate):
    """Update a distributor."""
    return _update_named_row(
        "distributors",
        distributor_id,
        distributor.name,
        "Distributor with this name already exists",
    )


def delete_distributor(distributor_id: int):
    """Delete a distributor."""
    return _delete_row("distributors", distributor_id)


def get_users(skip: int = 0, limit: int = 100):
    """Return paginated users."""
    return _fetch_paginated_rows("users", skip=skip, limit=limit)


def get_user(user_id: str | UUID):
    """Return a single user."""
    return _fetch_row("users", str(user_id))


def get_user_by_email(email: str):
    """Return a user by email."""
    return _fetch_row_by_column("users", "email", email.strip().lower())


def get_user_by_username(username: str):
    """Return a user by username."""
    cleaned_username = username.strip()
    if not cleaned_username:
        return None
    return _fetch_row_by_column("users", "username", cleaned_username)


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


def get_personal_collection_share_settings(auth_user: dict[str, Any]) -> dict[str, Any]:
    """Return share-link settings and subscribers for the authenticated user's collection."""
    collection = _get_or_create_personal_collection(auth_user)

    return {
        "collection_id": collection["id"],
        "share_enabled": bool(collection.get("share_enabled")),
        "share_token": collection.get("share_token"),
        "subscribers": _list_collection_subscribers(collection["id"]),
    }


def update_personal_collection_share_settings(
    auth_user: dict[str, Any],
    share_enabled: bool | None = None,
    regenerate_link: bool = False,
) -> dict[str, Any]:
    """Update the authenticated user's collection share link state."""
    collection = _get_or_create_personal_collection(auth_user)
    next_share_enabled = bool(collection.get("share_enabled")) if share_enabled is None else share_enabled
    next_share_token = collection.get("share_token")

    if regenerate_link or (next_share_enabled and not next_share_token):
        next_share_token = _create_share_token()

    with get_connection() as connection:
        try:
            connection.execute(
                """
                UPDATE collections
                SET share_enabled = ?, share_token = ?
                WHERE id = ?
                """,
                (1 if next_share_enabled else 0, next_share_token, collection["id"]),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            _raise_write_error(exc, "Share link could not be updated")

    return get_personal_collection_share_settings(auth_user)


def revoke_personal_collection_subscriber(auth_user: dict[str, Any], share_id: int) -> dict[str, Any]:
    """Revoke a subscriber from the authenticated user's personal collection."""
    collection = _get_or_create_personal_collection(auth_user)
    share = get_collection_share(share_id)

    if share is None or share["collection_id"] != collection["id"]:
        raise HTTPException(status_code=404, detail="Collection subscriber not found")

    deleted = delete_collection_share(share_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Collection subscriber not found")
    return deleted


def join_shared_collection(auth_user: dict[str, Any], share_token: str) -> dict[str, Any]:
    """Subscribe the authenticated user to a collection using its share link."""
    cleaned_token = share_token.strip()
    if not cleaned_token:
        raise HTTPException(status_code=400, detail="Share token is required")

    user = _get_or_create_authenticated_user(auth_user)
    collection = _get_collection_by_share_token(cleaned_token)
    if collection is None:
        raise HTTPException(status_code=404, detail="Shared collection not found")
    if str(collection["owner_id"]) == str(user["id"]):
        raise HTTPException(status_code=400, detail="You cannot subscribe to your own collection")

    share = _get_collection_share_by_user(collection["id"], user["id"])
    if share is None:
        share = create_collection_share(
            schemas.CollectionShareCreate(
                shared_with=UUID(str(user["id"])),
                permission=SHARE_PERMISSION_VIEWER,
            ),
            collection["id"],
        )

    owner = get_user(collection["owner_id"])
    if owner is None:
        raise HTTPException(status_code=404, detail="Collection owner not found")

    return _serialize_shared_collection_summary(share, collection, owner)


def get_shared_collections(auth_user: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the collections shared with the authenticated user."""
    user = _get_or_create_authenticated_user(auth_user)

    with get_connection() as connection:
        rows = _rows_to_dicts(
            connection.execute(
                """
                SELECT
                    cs.id AS share_id,
                    cs.permission,
                    c.id AS collection_id,
                    c.name,
                    c.description,
                    c.owner_id,
                    (
                        SELECT COUNT(*)
                        FROM collection_games cg
                        WHERE cg.collection_id = c.id
                    ) AS game_count,
                    u.id AS owner_user_id,
                    u.email AS owner_email,
                    u.username AS owner_username
                FROM collection_shares cs
                JOIN collections c ON c.id = cs.collection_id
                JOIN users u ON u.id = c.owner_id
                WHERE cs.shared_with = ?
                ORDER BY LOWER(COALESCE(u.username, u.email)) ASC, LOWER(c.name) ASC, c.id ASC
                """,
                (str(user["id"]),),
            ).fetchall()
        )

    return [
        {
            "collection_id": row["collection_id"],
            "share_id": row["share_id"],
            "permission": row["permission"],
            "name": row["name"],
            "description": row["description"],
            "owner": {
                "id": row["owner_user_id"],
                "email": row["owner_email"],
                "username": row["owner_username"],
            },
            "game_count": row["game_count"],
        }
        for row in rows
    ]


def get_shared_collection_board(auth_user: dict[str, Any], collection_id: int) -> dict[str, Any]:
    """Return the board for a collection shared with the authenticated user."""
    user = _get_or_create_authenticated_user(auth_user)
    share = _get_collection_share_by_user(collection_id, user["id"])
    if share is None:
        raise HTTPException(status_code=404, detail="Shared collection not found")

    collection = get_collection(collection_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Shared collection not found")

    owner = collection.get("owner")
    if owner is None:
        raise HTTPException(status_code=404, detail="Collection owner not found")

    board = _build_collection_board_payload(collection, owner)
    return {
        "collection_id": collection["id"],
        "share_id": share["id"],
        "permission": share["permission"],
        "name": collection["name"],
        "description": collection["description"],
        "owner": owner,
        **board,
    }


def unsubscribe_from_shared_collection(auth_user: dict[str, Any], collection_id: int) -> dict[str, Any]:
    """Remove the authenticated user's subscription to a shared collection."""
    user = _get_or_create_authenticated_user(auth_user)
    share = _get_collection_share_by_user(collection_id, user["id"])
    if share is None:
        raise HTTPException(status_code=404, detail="Shared collection not found")

    deleted = delete_collection_share(share["id"])
    if deleted is None:
        raise HTTPException(status_code=404, detail="Shared collection not found")
    return deleted


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


def get_personal_collection_games(
    auth_user: dict[str, Any],
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    game_type: str | None = None,
    year: str | None = None,
    sort_by: GameSortField = "name",
    sort_dir: GameSortDirection = "asc",
):
    """Return a paginated and filterable page for the authenticated user's collection."""
    collection = _get_or_create_personal_collection(auth_user)
    game_filter_clauses, game_filter_params = _build_game_filter_clauses(
        search=search,
        game_type=game_type,
        year=year,
    )
    where_clauses = ["cg.collection_id = ?", *game_filter_clauses]
    where_clause = f" WHERE {' AND '.join(where_clauses)}"
    parameters = [collection["id"], *game_filter_params]
    order_clause = _build_game_order(sort_by=sort_by, sort_dir=sort_dir)

    with get_connection() as connection:
        total = connection.execute(
            f"""
            SELECT COUNT(DISTINCT g.id)
            FROM games g
            JOIN collection_games cg ON cg.game_id = g.id
            {where_clause}
            """,
            tuple(parameters),
        ).fetchone()[0]

        game_rows = _rows_to_dicts(
            connection.execute(
                f"""
                SELECT DISTINCT g.*
                FROM games g
                JOIN collection_games cg ON cg.game_id = g.id
                {where_clause}
                ORDER BY {order_clause}
                LIMIT ? OFFSET ?
                """,
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


def get_personal_collection_board(auth_user: dict[str, Any]) -> dict[str, Any]:
    """Return the authenticated user's collection board with locations and game rows."""
    user = _get_or_create_authenticated_user(auth_user)
    collection = _get_or_create_personal_collection(auth_user)
    board = _build_collection_board_payload(collection, user)
    user_context = _auth_user_log_context(auth_user)
    runtime = _runtime_log_context()

    logger.info(
        "collection.board_loaded email=%s name=%s user_id=%s collection_id=%s items=%s locations=%s service=%s revision=%s hostname=%s sqlite_path=%s",
        user_context["email"],
        user_context["name"],
        user["id"],
        collection["id"],
        len(board["items"]),
        len(board["locations"]),
        runtime["service"],
        runtime["revision"],
        runtime["hostname"],
        runtime["sqlite_path"] or "-",
    )

    return {
        "collection_id": collection["id"],
        **board,
    }


def get_collection_game(collection_game_id: int):
    """Return a single collection game."""
    return _fetch_row("collection_games", collection_game_id)


def add_game_to_personal_collection(
    auth_user: dict[str, Any],
    game_id: int,
    quantity: int = 1,
    location_id: int | None = None,
):
    """Add a catalog game to the authenticated user's collection."""
    user = _get_or_create_authenticated_user(auth_user)
    collection = _get_or_create_personal_collection(auth_user)
    user_context = _auth_user_log_context(auth_user)
    runtime = _runtime_log_context()
    _require_personal_location(str(user["id"]), location_id)

    if get_game(game_id) is None:
        logger.warning(
            "collection.add_missing_game email=%s user_id=%s collection_id=%s game_id=%s service=%s revision=%s hostname=%s",
            user_context["email"],
            user["id"],
            collection["id"],
            game_id,
            runtime["service"],
            runtime["revision"],
            runtime["hostname"],
        )
        raise HTTPException(status_code=404, detail="Game not found")

    if _get_collection_game_by_game_id(collection["id"], game_id) is not None:
        logger.warning(
            "collection.add_duplicate_game email=%s user_id=%s collection_id=%s game_id=%s service=%s revision=%s hostname=%s",
            user_context["email"],
            user["id"],
            collection["id"],
            game_id,
            runtime["service"],
            runtime["revision"],
            runtime["hostname"],
        )
        raise HTTPException(status_code=409, detail="Game is already present in the personal collection")

    with get_connection() as connection:
        before_count = _count_collection_games(connection, collection["id"])

    created = create_collection_game(
        schemas.CollectionGameCreate(
            collection_id=collection["id"],
            game_id=game_id,
            location_id=location_id,
            quantity=quantity,
        )
    )
    with get_connection() as connection:
        after_count = _count_collection_games(connection, collection["id"])

    logger.info(
        "collection.added email=%s name=%s user_id=%s collection_id=%s collection_game_id=%s game_id=%s location_id=%s quantity=%s before_count=%s after_count=%s service=%s revision=%s hostname=%s sqlite_path=%s sqlite_seed_path=%s",
        user_context["email"],
        user_context["name"],
        user["id"],
        collection["id"],
        created["id"],
        game_id,
        location_id if location_id is not None else "null",
        quantity,
        before_count,
        after_count,
        runtime["service"],
        runtime["revision"],
        runtime["hostname"],
        runtime["sqlite_path"] or "-",
        runtime["sqlite_seed_path"] or "-",
    )
    return created


def create_personal_location(auth_user: dict[str, Any], name: str) -> dict[str, Any]:
    """Create a location owned by the authenticated user."""
    user = _get_or_create_authenticated_user(auth_user)
    cleaned_name = name.strip()
    if not cleaned_name:
        raise HTTPException(status_code=400, detail="Location name is required")

    return create_user_location(
        schemas.UserLocationCreate(
            user_id=UUID(str(user["id"])),
            name=cleaned_name,
        )
    )


def update_personal_location(auth_user: dict[str, Any], location_id: int, name: str) -> dict[str, Any]:
    """Rename a location owned by the authenticated user."""
    user = _get_or_create_authenticated_user(auth_user)
    cleaned_name = name.strip()
    if not cleaned_name:
        raise HTTPException(status_code=400, detail="Location name is required")
    if _get_user_location_for_user(str(user["id"]), location_id) is None:
        raise HTTPException(status_code=404, detail="User location not found")

    with get_connection() as connection:
        try:
            connection.execute(
                "UPDATE user_locations SET name = ? WHERE id = ? AND user_id = ?",
                (cleaned_name, location_id, str(user["id"])),
            )
            connection.commit()
        except sqlite3.IntegrityError as exc:
            connection.rollback()
            _raise_write_error(exc, "User location already exists or is invalid")

    updated = _get_user_location_for_user(str(user["id"]), location_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="User location not found")
    return updated


def delete_personal_location(auth_user: dict[str, Any], location_id: int) -> dict[str, Any]:
    """Delete a location owned by the authenticated user."""
    user = _get_or_create_authenticated_user(auth_user)
    location = _get_user_location_for_user(str(user["id"]), location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="User location not found")

    deleted = delete_user_location(location_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="User location not found")
    return deleted


def move_personal_collection_game(
    auth_user: dict[str, Any],
    collection_game_id: int,
    location_id: int | None = None,
) -> dict[str, Any]:
    """Move an existing personal collection game to another location."""
    user = _get_or_create_authenticated_user(auth_user)
    collection = _get_or_create_personal_collection(auth_user)
    collection_game = get_collection_game(collection_game_id)

    if collection_game is None or collection_game["collection_id"] != collection["id"]:
        raise HTTPException(status_code=404, detail="Collection game not found")

    _require_personal_location(str(user["id"]), location_id)

    existing = _get_collection_game_by_identity(collection["id"], collection_game["game_id"], location_id)
    if existing is not None and existing["id"] != collection_game_id:
        raise HTTPException(status_code=409, detail="Game is already present in the target location")

    with get_connection() as connection:
        connection.execute(
            "UPDATE collection_games SET location_id = ? WHERE id = ?",
            (location_id, collection_game_id),
        )
        connection.commit()

    updated = get_collection_game(collection_game_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Collection game not found")
    return updated


def remove_game_from_personal_collection(
    auth_user: dict[str, Any],
    collection_game_id: int,
) -> dict[str, Any]:
    """Remove an existing game row from the authenticated user's collection."""
    collection = _get_or_create_personal_collection(auth_user)
    collection_game = get_collection_game(collection_game_id)

    if collection_game is None or collection_game["collection_id"] != collection["id"]:
        raise HTTPException(status_code=404, detail="Collection game not found")

    deleted = delete_collection_game(collection_game_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Collection game not found")
    return deleted


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
