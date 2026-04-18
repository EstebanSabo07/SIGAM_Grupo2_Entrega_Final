"""SQLAlchemy engine and session helpers."""

from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from database.config import get_database_url, is_sqlite_url


def _engine_kwargs(database_url: str) -> dict:
    kwargs = {"future": True, "pool_pre_ping": True}
    if is_sqlite_url(database_url):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


@lru_cache(maxsize=4)
def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_database_url()
    return create_engine(url, **_engine_kwargs(url))


@lru_cache(maxsize=4)
def get_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(database_url), autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def session_scope(database_url: str | None = None) -> Iterator[Session]:
    """Provide a transactional session scope."""

    session = get_session_factory(database_url)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
