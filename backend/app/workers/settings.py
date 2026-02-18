"""arq worker settings — run with: arq app.workers.settings.WorkerSettings"""

import logging

from app.config import settings
from app.workers.tasks import (
    cleanup_expired_tokens,
    compute_all_preferences,
    process_all_covers,
    process_book_cover,
    send_queued_notification,
    send_recommendation_alert_email,
    send_weekly_digest_emails,
)

logger = logging.getLogger("bookswipe.worker")


async def startup(ctx: dict) -> None:
    logger.info("arq worker started")


async def shutdown(ctx: dict) -> None:
    logger.info("arq worker shutting down")


class WorkerSettings:
    """Configuration for the arq worker process."""

    functions = [
        cleanup_expired_tokens,
        compute_all_preferences,
        send_queued_notification,
        process_book_cover,
        process_all_covers,
        send_recommendation_alert_email,
        send_weekly_digest_emails,
    ]

    cron_jobs = [
        # Run cleanup_expired_tokens every hour at minute 0
        type("CronJob", (), {
            "coroutine": cleanup_expired_tokens,
            "hour": None,  # every hour
            "minute": {0},
            "unique": True,
        })(),
        # Run compute_all_preferences every hour at minute 30
        type("CronJob", (), {
            "coroutine": compute_all_preferences,
            "hour": None,  # every hour
            "minute": {30},
            "unique": True,
        })(),
        # Send weekly digest emails every Monday at 09:00 UTC
        type("CronJob", (), {
            "coroutine": send_weekly_digest_emails,
            "weekday": {0},  # Monday
            "hour": {9},
            "minute": {0},
            "unique": True,
        })(),
    ]

    on_startup = startup
    on_shutdown = shutdown

    # Redis connection — falls back to localhost if not configured
    redis_settings = None

    @classmethod
    def get_redis_settings(cls):
        if settings.redis_url:
            from arq.connections import RedisSettings
            return RedisSettings.from_dsn(settings.redis_url)
        return None
