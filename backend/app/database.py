"""Database configuration and session management for the anime quiz backend."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlmodel import SQLModel, Session, create_engine

_DEFAULT_SQLITE_URL = "sqlite:///./anime_quiz.db"


def _build_engine() -> tuple[str, dict[str, object]]:
    database_url = os.getenv("DATABASE_URL", _DEFAULT_SQLITE_URL)
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):  # enable SQLite usage in multi-threaded FastAPI
        connect_args = {"check_same_thread": False}
    return database_url, connect_args


DATABASE_URL, _CONNECT_ARGS = _build_engine()
engine = create_engine(DATABASE_URL, echo=False, connect_args=_CONNECT_ARGS)


def init_db() -> None:
    """Create database tables if they do not exist."""

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""

    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for manual session usage outside of dependencies."""

    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
