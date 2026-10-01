"""Non-sensitive application and database health routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from backend.app.db.database import check_database_connection


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Confirm that the FastAPI process is responsive."""
    return {"status": "ok"}


@router.get("/health/db")
def database_health() -> dict[str, str]:
    """Confirm database connectivity without exposing configuration or errors."""
    try:
        check_database_connection()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unavailable", "database": "unavailable"},
        ) from exc
    return {"status": "ok", "database": "connected"}
