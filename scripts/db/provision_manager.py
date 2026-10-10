"""Create or promote one local thesis-demo manager without storing credentials."""

import argparse
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select

from backend.app.core.config import get_settings
from backend.app.db.database import SessionLocal
from backend.app.db.models import User, UserRole
from backend.app.schemas.auth import RegisterRequest
from backend.app.services.auth import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely provision a local thesis-demo Manager account.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    args = parser.parse_args()
    settings = get_settings()
    if settings.app_env.lower() not in {"development", "local", "test"}:
        raise SystemExit("This utility is restricted to a local development or test environment.")
    password = getpass.getpass("Manager password (not echoed or saved): ")
    data = RegisterRequest(full_name=args.full_name, email=args.email, password=password)
    with SessionLocal.begin() as session:
        user = session.scalar(select(User).where(User.email == str(data.email).lower()))
        if user is None:
            session.add(User(
                full_name=data.full_name, email=str(data.email).lower(), password_hash=hash_password(data.password),
                role=UserRole.MANAGER, is_active=True,
            ))
            outcome = "created"
        else:
            user.full_name = data.full_name
            user.password_hash = hash_password(data.password)
            user.role = UserRole.MANAGER
            user.is_active = True
            outcome = "updated"
    print(f"Local manager account {outcome} for {str(data.email).lower()}. Password was not written to disk.")


if __name__ == "__main__":
    main()
