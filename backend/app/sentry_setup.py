"""Sentry error tracking initialization — graceful no-op when SENTRY_DSN is not set."""

import logging

from app.config import settings

logger = logging.getLogger("bookswipe")


def init_sentry() -> None:
    """Initialize Sentry SDK if SENTRY_DSN is configured, otherwise silently skip."""
    if not settings.sentry_dsn:
        logger.info("SENTRY_DSN not set — Sentry error tracking disabled")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            release=settings.app_version,
            traces_sample_rate=0.1 if settings.is_production else 1.0,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            send_default_pii=False,
        )
        logger.info("Sentry error tracking initialized")
    except Exception:
        logger.warning("Failed to initialize Sentry — continuing without it", exc_info=True)
