from base64 import b64decode
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.database import get_db_session
from backend.app.core.config import get_settings
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


def test_login_response_retains_the_safe_avatar_url_after_logout(client: TestClient, tmp_path, monkeypatch) -> None:
    assert register(client).status_code == 201
    monkeypatch.setattr(get_settings(), "avatar_upload_dir", tmp_path / "avatars")
    uploaded = client.post(
        "/api/auth/me/avatar",
        files={
            "file": (
                "avatar.png",
                b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl4w+gAAAAASUVORK5CYII="),
                "image/png",
            )
        },
        headers={"X-CSRF-Token": client.cookies.get("sim_csrf")},
    )
    assert uploaded.status_code == 200
    avatar_url = uploaded.json()["avatar_url"]
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": client.cookies.get("sim_csrf")}).status_code == 204
    login = client.post("/api/auth/login", json={"email": "manager@example.com", "password": "Long-test-password"})
    assert login.status_code == 200
    assert login.json()["avatar_url"] == avatar_url


def test_operational_writes_require_session_csrf_and_manager_role(client: TestClient) -> None:
    payload = {"code": "SECURE", "name": "Secured category"}
    assert client.post("/api/categories", json=payload).status_code == 401

    assert register(client).status_code == 201  # Public registration is inventory staff only.
    assert client.post("/api/categories", json=payload).status_code == 403  # Missing CSRF token.
    assert client.post(
        "/api/categories", json=payload, headers={"X-CSRF-Token": client.cookies.get("sim_csrf")}
    ).status_code == 403  # CSRF is valid, but the authenticated staff role is not operationally authorized.


def test_profile_updates_only_safe_fields(client: TestClient) -> None:
    assert register(client).status_code == 201
    csrf = {"X-CSRF-Token": client.cookies.get("sim_csrf")}
    updated = client.patch("/api/auth/me", json={"full_name": "  Updated User  "}, headers=csrf)
    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Updated User"
    assert updated.json()["role"] == "INVENTORY_STAFF"
    rejected = client.patch("/api/auth/me", json={"full_name": "Updated User", "role": "ADMIN"}, headers=csrf)
    assert rejected.status_code == 422
    assert client.get("/api/auth/me").json()["role"] == "INVENTORY_STAFF"


def test_avatar_upload_validation_replacement_and_removal(client: TestClient, tmp_path, monkeypatch) -> None:
    assert register(client).status_code == 201
    monkeypatch.setattr(get_settings(), "avatar_upload_dir", tmp_path / "avatars")
    csrf = {"X-CSRF-Token": client.cookies.get("sim_csrf")}
    malformed = client.post(
        "/api/auth/me/avatar",
        files={"file": ("avatar.png", b"not-a-png", "image/png")},
        headers=csrf,
    )
    assert malformed.status_code == 400
    oversized = client.post(
        "/api/auth/me/avatar",
        files={"file": ("avatar.png", b"x" * (3 * 1024 * 1024 + 1), "image/png")},
        headers=csrf,
    )
    assert oversized.status_code == 400
    assert "3 MB" in oversized.text
    uploaded = client.post(
        "/api/auth/me/avatar",
        files={
            "file": (
                "avatar.png",
                b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl4w+gAAAAASUVORK5CYII="),
                "image/png",
            )
        },
        headers=csrf,
    )
    assert uploaded.status_code == 200
    avatar_url = uploaded.json()["avatar_url"]
    assert avatar_url and avatar_url.startswith("/uploads/avatars/")
    assert str(tmp_path) not in avatar_url
    assert len(list((tmp_path / "avatars").iterdir())) == 1
    removed = client.delete("/api/auth/me/avatar", headers=csrf)
    assert removed.status_code == 200
    assert removed.json()["avatar_url"] is None
    assert not list((tmp_path / "avatars").iterdir())


def test_password_change_keeps_current_session_and_revokes_others(client: TestClient) -> None:
    assert register(client).status_code == 201
    with TestClient(app) as second_client:
        login = second_client.post("/api/auth/login", json={"email": "manager@example.com", "password": "Long-test-password"})
        assert login.status_code == 200
        changed = second_client.post(
            "/api/auth/change-password",
            json={"current_password": "Long-test-password", "new_password": "Changed-password"},
            headers={"X-CSRF-Token": second_client.cookies.get("sim_csrf")},
        )
        assert changed.status_code == 204
        assert second_client.get("/api/auth/me").status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"email": "manager@example.com", "password": "Long-test-password"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "manager@example.com", "password": "Changed-password"}).status_code == 200
