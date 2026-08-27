"""Auth API endpoints — Google OAuth2 with Redis sessions.

Session management uses an opaque token stored in Redis with a TTL.
The token is set as an httpOnly cookie. Revocation is trivial:
deleting the Redis key immediately invalidates the session.
"""

import json
import secrets

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.google_oauth import (
    exchange_code_for_token,
    get_google_auth_url,
    get_user_info,
)
from app.cache.redis_cache import redis_cache
from app.config import settings
from app.dependencies import get_db
from app.entities.user import UserRole
from app.repositories.user_repo import UserRepository

log = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Session helpers (Redis-backed)
# ---------------------------------------------------------------------------
SESSION_COOKIE = "session_id"
OAUTH_STATE_COOKIE = "oauth_state"


async def _create_session(user_id: int, email: str, name: str, role: str) -> str:
    """Create an opaque session token and store it in Redis."""
    token = secrets.token_urlsafe(32)
    session_data = json.dumps({
        "user_id": user_id,
        "email": email,
        "name": name,
        "role": role,
    })
    await redis_cache.set(
        f"session:{token}", session_data, ttl_seconds=settings.session_ttl_seconds
    )
    log.info("session_created", user_id=user_id, email=email)
    return token


async def _get_session(request: Request) -> dict:
    """Read session token from cookie and look up in Redis.

    Returns session data dict or raises 401.
    """
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    raw = await redis_cache.get(f"session:{token}")
    if raw is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


async def _delete_session(request: Request) -> None:
    """Delete the session from Redis (logout)."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        await redis_cache.delete(f"session:{token}")
        log.info("session_deleted", token_prefix=token[:8])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LoginResponse(BaseModel):
    url: str | None = None
    message: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    avatar_url: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/login", response_model=LoginResponse)
async def login(response: Response):
    """Return the Google OAuth authorization URL.

    If Google OAuth is not configured (client_id is empty), returns a
    message explaining that OAuth is not set up.
    """
    if not settings.google_client_id:
        return LoginResponse(
            message="Google OAuth is not configured. Set GOOGLE_CLIENT_ID in your environment.",
        )
    state = secrets.token_urlsafe(32)
    response.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=300,
    )
    url = get_google_auth_url(state=state)
    return LoginResponse(url=url)


@router.get("/callback")
async def callback(
    request: Request,
    code: str = "",
    state: str = "",
    db: AsyncSession = Depends(get_db),
):
    """Handle the Google OAuth callback.

    Exchanges the authorization code for tokens, fetches user info,
    creates or retrieves the user, and sets a Redis-backed session cookie.
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code",
        )

    # Validate OAuth state param (CSRF protection)
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if not expected_state or not secrets.compare_digest(state, expected_state):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing OAuth state parameter",
        )

    # Exchange code for tokens
    token_data = await exchange_code_for_token(code)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to obtain access token",
        )

    # Fetch user info from Google
    google_user = await get_user_info(access_token)
    google_id: str = google_user["sub"]
    email: str = google_user["email"]
    name: str = google_user.get("name", email)
    avatar_url: str | None = google_user.get("picture")

    # Find or create user
    repo = UserRepository(db)
    user = await repo.get_by_google_id(google_id)
    if user is None:
        user = await repo.get_by_email(email)
        if user is not None:
            user.google_id = google_id
            if avatar_url:
                user.avatar_url = avatar_url
            await db.flush()
        else:
            user = await repo.create_user(
                email=email,
                name=name,
                google_id=google_id,
                role=UserRole.ADMIN,
                avatar_url=avatar_url,
            )
    elif avatar_url and user.avatar_url != avatar_url:
        user.avatar_url = avatar_url
        await db.flush()

    await db.commit()

    # Create Redis session and set cookie
    token = await _create_session(user.id, user.email, user.name, user.role.value)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(OAUTH_STATE_COOKIE)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=settings.session_ttl_seconds,
    )
    return response


@router.get("/me", response_model=UserResponse)
async def me(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return the currently authenticated user's info."""
    session = await _get_session(request)
    repo = UserRepository(db)
    user = await repo.get_by_id(session["user_id"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        avatar_url=user.avatar_url,
    )


@router.post("/logout")
async def logout(request: Request):
    """Delete the session from Redis and clear the cookie."""
    await _delete_session(request)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE)
    return response
