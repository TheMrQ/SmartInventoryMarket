"""Promote one existing active local INVENTORY_STAFF account to MANAGER.

This local-only administrative operation intentionally preserves the account's
name, password hash, sessions, and every other user's role.  It is not an API.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.core.config import get_settings
from backend.app.db.database import SessionLocal
from backend.app.db.models import User, UserRole


def promote_existing_manager(email: str) -> tuple[str, str, str, bool]:
    """Promote exactly one active staff account, without altering credentials."""
    settings = get_settings()
    if settings.app_env.lower() not in {"development", "local", "test"}:
        raise RuntimeError("This utility is restricted to a local development or test environment.")
    normalized = email.strip().lower()
    with SessionLocal.begin() as session:
        user = session.scalar(select(User).where(User.email == normalized))
        if user is None:
            raise RuntimeError("No local account exists for the supplied email.")
        if not user.is_active:
            raise RuntimeError("The supplied local account is inactive and will not be changed.")
        if user.role == UserRole.MANAGER:
            return user.email, user.full_name, user.role.value, bool(user.is_active)
        if user.role != UserRole.INVENTORY_STAFF:
            raise RuntimeError("Only an existing INVENTORY_STAFF account may be promoted by this utility.")
        user.role = UserRole.MANAGER
        return user.email, user.full_name, user.role.value, bool(user.is_active)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="existing local account email")
    args = parser.parse_args()
    email, full_name, role, active = promote_existing_manager(args.email)
    print(f"{email} | {full_name} | {role} | {active}")


if __name__ == "__main__":
    main()
