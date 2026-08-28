"""
Groq Model Watchdog — periodic check if configured model is still available.

Does NOT auto-switch models. Only logs a warning and (TODO) sends email alert.
"""

import asyncio
from datetime import UTC, datetime

import httpx
import structlog

from app.cache.redis_cache import redis_cache
from app.config import settings

log = structlog.get_logger()

REDIS_KEY = "groq:model:checked_at"
CHECK_INTERVAL_DAYS = 10
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
REQUEST_TIMEOUT = 10.0


async def _check_model_availability() -> None:
    """Check if the configured Groq model is still available."""
    try:
        raw = await redis_cache.get(REDIS_KEY)
        if raw:
            checked_at = datetime.fromisoformat(raw) if isinstance(raw, str) else None
            if checked_at:
                days_since = (datetime.now(UTC) - checked_at).days
                if days_since < CHECK_INTERVAL_DAYS:
                    return

        # Fetch available models
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(
                GROQ_MODELS_URL,
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            )
            resp.raise_for_status()
            models_data = resp.json()

        available_ids = {m["id"] for m in models_data.get("data", [])}

        # Update checked_at
        await redis_cache.set(
            REDIS_KEY,
            datetime.now(UTC).isoformat(),
            ttl_seconds=CHECK_INTERVAL_DAYS * 86400,
        )

        if settings.groq_model not in available_ids:
            # Model is NOT available — find which fallbacks are active
            active_fallbacks = [
                f for f in settings.groq_model_fallbacks if f in available_ids
            ]
            log.warning(
                "groq_model_unavailable",
                model=settings.groq_model,
                active_fallbacks=active_fallbacks,
                message=(
                    f"O modelo Groq configurado '{settings.groq_model}' não está mais disponível. "
                    f"Sugestões ativas: {active_fallbacks}. "
                    f"Atualize GROQ_MODEL manualmente."
                ),
            )
            # TODO: enviar e-mail de alerta quando o serviço de e-mail estiver configurado
        else:
            log.info("groq_model_ok", model=settings.groq_model)

    except Exception as e:
        log.warning("groq_watchdog_error", error=str(e))


def schedule_model_check() -> None:
    """Schedule a non-blocking model availability check."""
    asyncio.create_task(_check_model_availability())
