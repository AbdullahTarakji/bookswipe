"""Background tasks for the BookSwipe worker process."""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

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
