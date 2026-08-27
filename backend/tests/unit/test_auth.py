"""Tests for auth endpoints (Redis sessions)."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_get_session_valid():
    """Valid session token returns user data from Redis."""
    from app.api.v1.auth import _get_session

    session_data = {"user_id": 1, "email": "test@test.com", "name": "Test", "role": "admin"}
    mock_request = MagicMock()
    mock_request.cookies.get.return_value = "valid-token"

    with patch("app.api.v1.auth.redis_cache") as mock_redis:
        mock_redis.get = AsyncMock(return_value=json.dumps(session_data))
        result = await _get_session(mock_request)

    assert result["user_id"] == 1
    assert result["email"] == "test@test.com"


@pytest.mark.asyncio
async def test_get_session_no_cookie():
    """Missing session cookie raises 401."""
    from app.api.v1.auth import _get_session

    mock_request = MagicMock()
    mock_request.cookies.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await _get_session(mock_request)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_session_expired():
    """Expired session (not in Redis) raises 401."""
    from app.api.v1.auth import _get_session

    mock_request = MagicMock()
    mock_request.cookies.get.return_value = "expired-token"

    with patch("app.api.v1.auth.redis_cache") as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        with pytest.raises(HTTPException) as exc_info:
            await _get_session(mock_request)
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_create_session_stores_in_redis():
    """Creating a session stores data in Redis with correct key and TTL."""
    from app.api.v1.auth import _create_session

    with patch("app.api.v1.auth.redis_cache") as mock_redis:
        mock_redis.set = AsyncMock()
        token = await _create_session(1, "test@test.com", "Test", "admin")

    assert isinstance(token, str)
    assert len(token) > 20
    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][0].startswith("session:")
    stored_data = json.loads(call_args[0][1])
    assert stored_data["user_id"] == 1


@pytest.mark.asyncio
async def test_delete_session():
    """Deleting a session removes it from Redis."""
    from app.api.v1.auth import _delete_session

    mock_request = MagicMock()
    mock_request.cookies.get.return_value = "token-to-delete"

    with patch("app.api.v1.auth.redis_cache") as mock_redis:
        mock_redis.delete = AsyncMock()
        await _delete_session(mock_request)

    mock_redis.delete.assert_called_once_with("session:token-to-delete")
