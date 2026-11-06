from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
import backend.app.db.models  # noqa: F401
from backend.app.db.models import User, UserRole
from scripts.db.promote_existing_manager import promote_existing_manager


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    yield factory
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_promote_existing_manager_preserves_credentials_and_other_accounts(session_factory, monkeypatch) -> None:
    db_session = session_factory()
    staff = User(email="owner@example.test", full_name="Owner", password_hash="unchanged", role=UserRole.INVENTORY_STAFF, is_active=True)
    other = User(email="other@example.test", full_name="Other", password_hash="other", role=UserRole.INVENTORY_STAFF, is_active=True)
    db_session.add_all([staff, other]); db_session.commit()
    monkeypatch.setattr("scripts.db.promote_existing_manager.SessionLocal", session_factory)

    email, name, role, active = promote_existing_manager("OWNER@example.test")

    db_session.expire_all()
    promoted = db_session.scalar(select(User).where(User.email == "owner@example.test"))
    untouched = db_session.scalar(select(User).where(User.email == "other@example.test"))
    assert (email, name, role, active) == ("owner@example.test", "Owner", "MANAGER", True)
    assert promoted.role == UserRole.MANAGER and promoted.password_hash == "unchanged"
    assert untouched.role == UserRole.INVENTORY_STAFF and untouched.password_hash == "other"


def test_promote_existing_manager_rejects_inactive_account(session_factory, monkeypatch) -> None:
    db_session = session_factory()
    db_session.add(User(email="inactive@example.test", full_name="Inactive", password_hash="x", role=UserRole.INVENTORY_STAFF, is_active=False)); db_session.commit()
    monkeypatch.setattr("scripts.db.promote_existing_manager.SessionLocal", session_factory)

    with pytest.raises(RuntimeError, match="inactive"):
        promote_existing_manager("inactive@example.test")
