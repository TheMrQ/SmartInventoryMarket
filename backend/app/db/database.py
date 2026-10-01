"""SQLAlchemy engine, session dependency, and lightweight connection check."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings


def create_database_engine(database_url: str) -> Engine:
    """Build an engine without opening a connection during application import."""
    return create_engine(database_url, pool_pre_ping=True)


engine = create_database_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db_session() -> Generator[Session, None, None]:
    """Yield one request-scoped session and always close it afterwards."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def check_database_connection() -> None:
    """Execute the smallest practical non-mutating database health probe."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def dispose_database_engine() -> None:
    """Release pooled connections for tests or orderly process shutdown."""
    engine.dispose()
