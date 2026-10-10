"""Verify and clean up a real local-MySQL authentication session flow."""

import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from backend.app.db.database import SessionLocal
from backend.app.db.models import AuthSession, User
from backend.app.main import app


def require(response, expected: int):
    if response.status_code != expected:
        raise RuntimeError(f"expected HTTP {expected}; received HTTP {response.status_code}: {response.text}")
    return response


def cleanup(email: str) -> None:
    """Remove only this script's uniquely generated user and sessions."""
    with SessionLocal.begin() as session:
        user_ids = list(session.scalars(select(User.id).where(User.email == email)))
        session.execute(delete(AuthSession).where(AuthSession.user_id.in_(user_ids)))
        session.execute(delete(User).where(User.id.in_(user_ids)))


def main() -> None:
    marker = uuid4().hex
    email = f"p18-auth-smoke-{marker}@example.invalid"
    password = f"P18Smoke{uuid4().hex}A"
    try:
        with TestClient(app) as client:
            response = require(client.post("/api/auth/register", json={
                "full_name": "P18 authentication smoke user", "email": email, "password": password,
            }), 201)
            if not client.cookies.get("sim_session") or not client.cookies.get("sim_csrf"):
                raise RuntimeError("registration did not establish both session and CSRF cookies")
            with SessionLocal() as session:
                user = session.scalar(select(User).where(User.email == email))
                auth_session = session.scalar(select(AuthSession).where(AuthSession.user_id == user.id)) if user else None
                if not user or password in user.password_hash or not user.password_hash.startswith("scrypt$"):
                    raise RuntimeError("registration did not persist a non-plaintext password hash")
                if not auth_session or auth_session.revoked_at is not None:
                    raise RuntimeError("registration did not persist an active server-side session")
            require(client.get("/api/auth/me"), 200)
            csrf = client.cookies.get("sim_csrf")
            logout = require(client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}), 204)
            if "sim_session=" not in logout.headers.get("set-cookie", ""):
                raise RuntimeError("logout response did not expire the session cookie")
            require(client.get("/api/auth/me"), 401)
        print("P18 live MySQL auth flow passed: registration, hash, session, cookies, /me, and logout verified.")
    finally:
        cleanup(email)
        print("P18 live MySQL auth smoke data cleanup passed.")


if __name__ == "__main__":
    main()
