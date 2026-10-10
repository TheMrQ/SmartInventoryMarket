"""Cookie-session authentication and server-side authorization dependencies."""

from collections import defaultdict, deque
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.db.database import get_db_session
from backend.app.db.models import AuthSession, User, UserRole, utc_now
from backend.app.schemas.auth import AuthenticatedUser, LoginRequest, RegisterRequest, UserRead
from backend.app.services.auth import expiry, hash_password, new_csrf_token, new_session_token, token_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
SessionDep = Annotated[Session, Depends(get_db_session)]
_attempts: dict[str, deque[datetime]] = defaultdict(deque)


def _set_cookies(response: Response, token: str, csrf: str) -> None:
    settings = get_settings()
    response.set_cookie("sim_session", token, httponly=True, secure=settings.cookie_secure, samesite="lax", max_age=settings.session_hours * 3600, path="/")
    response.set_cookie("sim_csrf", csrf, httponly=False, secure=settings.cookie_secure, samesite="lax", max_age=settings.session_hours * 3600, path="/")


def _clear_cookies(response: Response) -> None:
    response.delete_cookie("sim_session", path="/")
    response.delete_cookie("sim_csrf", path="/")


def _rate_limited(key: str) -> bool:
    now = utc_now()
    window = _attempts[key]
    while window and (now - window[0]).total_seconds() > 300:
        window.popleft()
    return len(window) >= 8


def current_user(request: Request, session: SessionDep, sim_session: str | None = Cookie(default=None), sim_csrf: str | None = Cookie(default=None)) -> User:
    if not sim_session:
        raise HTTPException(status_code=401, detail="Authentication is required.")
    auth_session = session.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(sim_session)))
    if not auth_session or auth_session.revoked_at or auth_session.expires_at <= utc_now() or not auth_session.user.is_active:
        raise HTTPException(status_code=401, detail="Authentication is required.")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        header = request.headers.get("X-CSRF-Token")
        if not sim_csrf or not header or not hmac_compare(header, sim_csrf):
            raise HTTPException(status_code=403, detail="Invalid request verification token.")
    return auth_session.user


def operational_user(user: Annotated[User, Depends(current_user)], request: Request) -> User:
    if request.method not in {"GET", "HEAD", "OPTIONS"} and user.role not in {UserRole.ADMIN, UserRole.MANAGER}:
        raise HTTPException(status_code=403, detail="Manager access is required for this action.")
    return user


def hmac_compare(left: str, right: str) -> bool:
    import hmac
    return hmac.compare_digest(left, right)


@router.post("/register", response_model=AuthenticatedUser, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, response: Response, session: SessionDep):
    email = str(data.email).lower()
    if session.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    user = User(email=email, full_name=data.full_name, password_hash=hash_password(data.password), role=UserRole.INVENTORY_STAFF, is_active=True)
    session.add(user)
    session.flush()
    token, csrf = new_session_token(), new_csrf_token()
    session.add(AuthSession(user_id=user.id, token_hash=token_hash(token), expires_at=expiry(get_settings().session_hours)))
    session.commit()
    _set_cookies(response, token, csrf)
    return AuthenticatedUser(id=user.id, full_name=user.full_name, email=user.email, role=user.role, csrf_token=csrf)


@router.post("/login", response_model=AuthenticatedUser)
def login(data: LoginRequest, response: Response, request: Request, session: SessionDep):
    key = f"{request.client.host if request.client else 'unknown'}:{str(data.email).lower()}"
    if _rate_limited(key):
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Try again later.")
    user = session.scalar(select(User).where(User.email == str(data.email).lower()))
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        _attempts[key].append(utc_now())
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    _attempts.pop(key, None)
    token, csrf = new_session_token(), new_csrf_token()
    session.add(AuthSession(user_id=user.id, token_hash=token_hash(token), expires_at=expiry(get_settings().session_hours)))
    session.commit()
    _set_cookies(response, token, csrf)
    return AuthenticatedUser(id=user.id, full_name=user.full_name, email=user.email, role=user.role, csrf_token=csrf)


@router.get("/me", response_model=UserRead)
def me(user: Annotated[User, Depends(current_user)]):
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, session: SessionDep, user: Annotated[User, Depends(current_user)], sim_session: str | None = Cookie(default=None)):
    if sim_session:
        auth_session = session.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(sim_session)))
        if auth_session:
            auth_session.revoked_at = utc_now()
            session.commit()
    _clear_cookies(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
