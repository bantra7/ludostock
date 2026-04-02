import sqlite3

import pytest
from fastapi import HTTPException

from backend.app import crud


def test_raise_write_error_maps_unique_to_409():
    exc = sqlite3.IntegrityError("UNIQUE constraint failed: authors.name")

    with pytest.raises(HTTPException) as exc_info:
        crud._raise_write_error(exc, "Author with this name already exists")

    assert exc_info.value.status_code == 409


def test_raise_write_error_maps_foreign_key_to_400():
    exc = sqlite3.IntegrityError("FOREIGN KEY constraint failed")

    with pytest.raises(HTTPException) as exc_info:
        crud._raise_write_error(exc, "Collection could not be created")

    assert exc_info.value.status_code == 400
