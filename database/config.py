"""Database configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_SQLITE_PATH = Path(__file__).resolve().parent / "igsm_dev.sqlite3"


def get_database_url() -> str:
    """Return the configured database URL.

    Returns:
        Database URL from ``DATABASE_URL`` or the local SQLite fallback.
    """

    return os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}")


def is_sqlite_url(database_url: str) -> bool:
    """Check whether a database URL targets SQLite.

    Args:
        database_url: SQLAlchemy database URL.

    Returns:
        True when the URL uses the SQLite dialect.
    """

    return database_url.startswith("sqlite:")
