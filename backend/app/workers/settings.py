"""arq worker settings — run with: arq app.workers.settings.WorkerSettings"""

import logging
from datetime import timedelta

from app.config import settings
from app.workers.tasks import cleanup_expired_tokens

logger = logging.getLogger("bookswipe.worker")


async def startup(ctx: dict) -> None:
    logger.info("arq worker started")


async def shutdown(ctx: dict) -> None:
    logger.info("arq worker shutting down")


class WorkerSettings:
    """Configuration for the arq worker process."""

    functions = [cleanup_expired_tokens]

    cron_jobs = [
        # Run cleanup_expired_tokens every hour at minute 0
        type("CronJob", (), {
            "coroutine": cleanup_expired_tokens,
            "hour": None,  # every hour
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
