"""Background tasks for the BookSwipe worker process."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, distinct

logger = logging.getLogger("bookswipe.worker")


async def cleanup_expired_tokens(ctx: dict) -> int:
    """Delete blacklisted tokens older than the max token lifetime (7 days).

    Runs hourly to keep the blacklist table lean.
    Returns the number of deleted rows.
    """
    from app.database import SessionLocal
    from app.models import BlacklistedToken

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    db = SessionLocal()
    try:
        result = db.execute(
            delete(BlacklistedToken).where(BlacklistedToken.blacklisted_at < cutoff)
        )
        db.commit()
        deleted = result.rowcount  # type: ignore[union-attr]
        logger.info("cleanup_expired_tokens removed %d expired tokens", deleted)
        return deleted
    finally:
        db.close()


async def compute_all_preferences(ctx: dict) -> int:
    """Batch-compute preference profiles for all users with swipe events.

    Runs hourly to keep recommendation quality fresh.
    Returns the number of users processed.
    """
    from app.database import SessionLocal
    from app.models import SwipeEvent
    from app.services.recommendation import compute_and_store_preferences

    db = SessionLocal()
    try:
        user_ids = db.query(distinct(SwipeEvent.user_id)).all()
        count = 0
        for (uid,) in user_ids:
            compute_and_store_preferences(db, uid)
            count += 1
        logger.info("compute_all_preferences processed %d users", count)
        return count
    finally:
        db.close()
