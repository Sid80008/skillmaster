"""
Database engine, session factory, and base class.

Usage (FastAPI dependency)
--------------------------
    from app.core.database import get_db
    def my_endpoint(db: Session = Depends(get_db)): ...

For raw access outside request context:
    from app.core.database import SessionLocal
    with SessionLocal() as session:
        ...
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


def _make_engine(url: str):
    """Create a SQLAlchemy engine with sane defaults."""
    return create_engine(
        url,
        pool_pre_ping=True,       # reconnect on stale connections
        pool_size=10,
        max_overflow=20,
        echo=False,
    )


settings = get_settings()
engine = _make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


# ── FastAPI dependency ────────────────────────────────────────────────────────


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, ensuring it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Utility ───────────────────────────────────────────────────────────────────


def check_connection() -> bool:
    """Return True if the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
