import sentry_sdk
import structlog
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.config import settings

log = structlog.get_logger()

APP_VERSION = "2.0.0"


def init_sentry() -> None:
    if not settings.sentry_dsn:
        log.info("Sentry DSN not configured — skipping initialization")
        return

    traces_rate = 1.0 if settings.app_env == "development" else 0.1

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        release=f"crm-ai-mvp@{APP_VERSION}",
        traces_sample_rate=traces_rate,
        integrations=[
            FastApiIntegration(),
            LoggingIntegration(level=None, event_level=None),
        ],
    )

    log.info("Sentry initialized", environment=settings.app_env, traces_rate=traces_rate)
