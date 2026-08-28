"""Auth package — Google OAuth2 skeleton."""

from app.auth.google_oauth import (
    exchange_code_for_token,
    get_google_auth_url,
    get_user_info,
)

__all__ = [
    "exchange_code_for_token",
    "get_google_auth_url",
    "get_user_info",
]
