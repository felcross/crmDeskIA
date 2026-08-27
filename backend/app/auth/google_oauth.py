"""Google OAuth2 flow helpers.

Skeleton implementation — detailed auth design is deferred.
Uses httpx async client for all Google API calls.
"""

from urllib.parse import urlencode

import httpx

from app.config import settings

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"

SCOPES = ["openid", "email", "profile"]


def _redirect_uri() -> str:
    """Build the OAuth callback URL from frontend_origin config."""
    return f"{settings.frontend_origin}/api/v1/auth/callback"


def get_google_auth_url(state: str = "") -> str:
    """Generate Google OAuth2 authorization URL.

    Args:
        state: Opaque CSRF token forwarded back by Google.

    Returns:
        Full URL the client should redirect the user to.
    """
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> dict:
    """Exchange an authorization code for tokens.

    Returns:
        dict with at least ``access_token`` and ``id_token`` keys.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": _redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_user_info(access_token: str) -> dict:
    """Fetch the authenticated user's profile from Google.

    Returns:
        dict with ``sub``, ``email``, ``name``, ``picture``, etc.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()
