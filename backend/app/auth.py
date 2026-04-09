"""Authentication helpers backed by the Better Auth service."""

from typing import Any

import httpx
from fastapi import HTTPException, Request

from .config import AUTH_INTERNAL_SECRET, AUTH_SERVICE_TIMEOUT_SECONDS, AUTH_SERVICE_URL


AUTH_EXEMPT_PATHS = frozenset(
    {
        "/api/meta/version/",
    }
)
ADMIN_EMAIL = "renault.jbapt@gmail.com"
ADMIN_ONLY_PATH_PREFIXES = (
    "/api/users/",
    "/api/collections/",
    "/api/collection_shares/",
    "/api/user_locations/",
    "/api/collection_games/",
)
ADMIN_ONLY_REFERENCE_PREFIXES = (
    "/api/authors/",
    "/api/artists/",
    "/api/editors/",
    "/api/distributors/",
    "/api/games/",
)


def is_admin_user(user: dict[str, Any] | None) -> bool:
    """Return whether the authenticated user can administer the global catalog."""
    email = user.get("email") if isinstance(user, dict) else None
    return isinstance(email, str) and email.casefold() == ADMIN_EMAIL.casefold()


def requires_admin_access(path: str, method: str) -> bool:
    """Return whether an API request targets global data reserved to the administrator."""
    if path.startswith("/api/me/collection/"):
        return False
    if any(path.startswith(prefix) for prefix in ADMIN_ONLY_PATH_PREFIXES):
        return True
    if method in {"POST", "PUT", "PATCH", "DELETE"} and any(
        path.startswith(prefix) for prefix in ADMIN_ONLY_REFERENCE_PREFIXES
    ):
        return True
    return False


async def get_authenticated_session(request: Request) -> dict[str, Any]:
    """Validate the current request session against the auth service."""
    cookie_header = request.headers.get("cookie")
    if not cookie_header:
        raise HTTPException(status_code=401, detail="Authentication required")

    headers = {
        "Accept": "application/json",
        "Cookie": cookie_header,
    }
    if AUTH_INTERNAL_SECRET:
        headers["X-Internal-Auth-Secret"] = AUTH_INTERNAL_SECRET

    url = f"{AUTH_SERVICE_URL.rstrip('/')}/internal/session"

    try:
        async with httpx.AsyncClient(timeout=AUTH_SERVICE_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=headers)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Authentication service unavailable") from exc

    if response.status_code == 401:
        raise HTTPException(status_code=401, detail="Authentication required")
    if response.status_code == 403:
        raise HTTPException(status_code=503, detail="Authentication service misconfigured")
    if response.status_code >= 500:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Authentication validation failed")

    payload = response.json()
    if not isinstance(payload, dict) or "user" not in payload:
        raise HTTPException(status_code=502, detail="Authentication validation failed")

    return payload
