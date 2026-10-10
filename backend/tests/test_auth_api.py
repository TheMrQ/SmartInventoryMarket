from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.database import get_db_session
import backend.app.db.models  # noqa: F401
from backend.app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    def override() -> Generator[Session, None, None]:
        session = factory()
        try: yield session
        finally: session.close()
    app.dependency_overrides[get_db_session] = override
    with TestClient(app) as value: yield value
    app.dependency_overrides.clear(); Base.metadata.drop_all(engine); engine.dispose()


def register(client: TestClient, email: str = "manager@example.com"):
    return client.post("/api/auth/register", json={"full_name": "Test User", "email": email, "password": "Long-test-password"})


def test_registration_hashes_password_and_rejects_duplicates(client: TestClient) -> None:
    created = register(client)
    assert created.status_code == 201
    assert created.json()["role"] == "INVENTORY_STAFF"
    assert "password" not in created.text
    assert register(client).status_code == 409


@pytest.mark.parametrize("password", ["shortA1", "long-test-password"])
def test_registration_enforces_the_displayed_password_policy(client: TestClient, password: str) -> None:
    response = client.post("/api/auth/register", json={"full_name": "Test User", "email": f"{password}@example.com", "password": password})
    assert response.status_code == 422
    assert "uppercase" in response.text or "at least 8" in response.text


def test_login_session_me_logout_and_unauthorized_access(client: TestClient) -> None:
    register(client)
    assert client.post("/api/categories", json={"code": "NOPE", "name": "No access"}, headers={"X-CSRF-Token": client.cookies.get("sim_csrf")}).status_code == 403
    client.post("/api/auth/logout", headers={"X-CSRF-Token": client.cookies.get("sim_csrf")})
    assert client.post("/api/auth/login", json={"email": "manager@example.com", "password": "wrong-password"}).status_code == 401
    login = client.post("/api/auth/login", json={"email": "manager@example.com", "password": "Long-test-password"})
    assert login.status_code == 200
    assert client.get("/api/auth/me").json()["email"] == "manager@example.com"
    assert client.get("/api/products").status_code == 200
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": client.cookies.get("sim_csrf")}).status_code == 204
    assert client.cookies.get("sim_session") is None
    assert client.get("/api/products").status_code == 401
