"""Runtime helpers that keep the local SIGAM database ready for the app."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.engine import make_url

from database.config import DEFAULT_SQLITE_PATH, get_database_url
from database.import_source_baseline import load_source_baseline
from database.models import Base, FactIndicatorResponse
from database.seed import seed_all
from database.session import get_engine, session_scope


def _is_default_local_sqlite_url(database_url: str) -> bool:
    """Return whether a database URL targets the default local SQLite file.

    Args:
        database_url: SQLAlchemy database URL.

    Returns:
        True when the URL points at ``database/igsm_dev.sqlite3``.
    """

    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database:
        return False
    return Path(url.database).resolve() == DEFAULT_SQLITE_PATH.resolve()


def ensure_database_ready(
    database_url: str | None = None,
    load_local_baseline: bool = True,
) -> dict[str, Any]:
    """Create the schema, seed reference data, and restore the local baseline.

    Args:
        database_url: Optional database URL override.
        load_local_baseline: Whether to auto-load the bundled 2025 baseline when
            the default local SQLite database has no fact rows yet.

    Returns:
        Summary metadata about the initialization work performed.
    """

    resolved_url = database_url or get_database_url()
    engine = get_engine(resolved_url)
    Base.metadata.create_all(engine)

    with session_scope(resolved_url) as session:
        seed_all(session=session)
        response_count = int(session.scalar(select(func.count()).select_from(FactIndicatorResponse)) or 0)

    baseline_loaded = False
    if load_local_baseline and response_count == 0 and _is_default_local_sqlite_url(resolved_url):
        load_source_baseline(replace=False, database_url=resolved_url)
        baseline_loaded = True
        with session_scope(resolved_url) as session:
            response_count = int(session.scalar(select(func.count()).select_from(FactIndicatorResponse)) or 0)

    return {
        "database_url": resolved_url,
        "baseline_loaded": baseline_loaded,
        "response_count": response_count,
    }
