"""Background tasks for the BookSwipe worker process."""

from __future__ import annotations

import asyncio
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


async def send_queued_notification(
    ctx: dict,
    user_id: int,
    title: str,
    body: str,
    category: str = "general",
    deep_link: str | None = None,
) -> int:
    """Send a notification to a user via the background worker queue.

    Stores the notification in history and delivers push to all registered devices.
    Returns the notification ID.
    """
    from app.database import SessionLocal
    from app.services.notification import notify_user

    db = SessionLocal()
    try:
        notif = notify_user(db, user_id, title, body, category=category, deep_link=deep_link)
        logger.info("send_queued_notification delivered id=%d to user=%d", notif.id, user_id)
        return notif.id
    finally:
        db.close()


async def process_book_cover(ctx: dict, book_id: str) -> bool:
    """Fetch, resize, and upload cover images for a single book.

    Creates or updates the BookCover record with S3 URLs and blurhash.
    Returns True on success, False if no cover image was available.
    """
    from app.database import SessionLocal
    from app.models import BookCover
    from app.services.image_service import process_and_upload_cover

    result = await process_and_upload_cover(book_id)
    if not result:
        logger.warning("process_book_cover: no cover for book %s", book_id)
        return False

    db = SessionLocal()
    try:
        existing = db.query(BookCover).filter(BookCover.book_id == book_id).first()
        if existing:
            existing.thumbnail_url = result["thumbnail_url"]
            existing.card_url = result["card_url"]
            existing.detail_url = result["detail_url"]
            existing.blurhash = result["blurhash"]
            existing.processed_at = datetime.now(timezone.utc)
        else:
            db.add(BookCover(
                book_id=book_id,
                thumbnail_url=result["thumbnail_url"],
                card_url=result["card_url"],
                detail_url=result["detail_url"],
                blurhash=result["blurhash"],
            ))
        db.commit()
        logger.info("process_book_cover: saved covers for book %s", book_id)
        return True
    finally:
        db.close()


async def process_all_covers(ctx: dict) -> int:
    """Batch-process covers for all books that don't yet have CDN images.

    Scans liked books and processes any without a BookCover record.
    Returns the number of books processed.
    """
    from app.database import SessionLocal
    from app.models import BookCover, LikedBook

    db = SessionLocal()
    try:
        # Find all unique book IDs from liked books that have no cover record
        existing_ids = {row[0] for row in db.query(BookCover.book_id).all()}
        all_book_ids = {
            row[0] for row in db.query(distinct(LikedBook.google_book_id)).all()
        }
        unprocessed = all_book_ids - existing_ids
    finally:
        db.close()

    count = 0
    for bid in unprocessed:
        try:
            ok = await process_book_cover(ctx, bid)
            if ok:
                count += 1
            # Small delay to avoid hammering Google Books
            await asyncio.sleep(0.5)
        except Exception:
            logger.exception("process_all_covers: failed for book %s", bid)

    logger.info("process_all_covers: processed %d books", count)
    return count
