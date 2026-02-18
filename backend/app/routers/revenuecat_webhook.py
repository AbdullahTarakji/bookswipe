"""RevenueCat webhook endpoint for server-to-server subscription notifications.

RevenueCat sends events when subscriptions are created, renewed, cancelled,
expired, or encounter billing issues.  This router validates the webhook
signature, parses the event, and updates the user's subscription state in
the database.
"""

from __future__ import annotations

import datetime
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import PaymentError
from app.models import User
from app.services.revenuecat_service import (
    EVENT_BILLING_ISSUE,
    EVENT_CANCELLATION,
    EVENT_EXPIRATION,
    EVENT_INITIAL_PURCHASE,
    EVENT_RENEWAL,
    parse_webhook_event,
    verify_webhook_signature,
)

logger = logging.getLogger("bookswipe")
router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


def _find_user_by_id(app_user_id: str, db: Session) -> User | None:
    """Look up a user by their app user ID (used as RevenueCat app_user_id)."""
    try:
        user_id = int(app_user_id)
    except (ValueError, TypeError):
        return None
    return db.query(User).filter(User.id == user_id).first()


@router.post("/revenuecat")
async def revenuecat_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle RevenueCat server-to-server webhook notifications."""
    payload = await request.body()
    signature = request.headers.get("X-RevenueCat-Signature", "")

    if not verify_webhook_signature(payload, signature):
        raise PaymentError("Invalid RevenueCat webhook signature")

    body = await request.json()
    parsed = parse_webhook_event(body)

    if parsed is None:
        # Unhandled event type — acknowledge silently
        return {"status": "ignored"}

    event_type = parsed["event_type"]
    app_user_id = parsed["app_user_id"]
    expiration_at_ms = parsed.get("expiration_at_ms")

    user = _find_user_by_id(app_user_id, db)
    if not user:
        logger.warning("RevenueCat webhook: no user for app_user_id %s", app_user_id)
        return {"status": "user_not_found"}

    if event_type in (EVENT_INITIAL_PURCHASE, EVENT_RENEWAL):
        user.subscription_status = "active"
        user.subscription_plan = "premium"
        if expiration_at_ms:
            user.subscription_end_date = datetime.datetime.fromtimestamp(
                expiration_at_ms / 1000, tz=datetime.timezone.utc
            )
        logger.info("RevenueCat %s: activated premium for user %d", event_type, user.id)

    elif event_type == EVENT_CANCELLATION:
        user.subscription_status = "cancelled"
        # Plan stays premium until expiration
        if expiration_at_ms:
            user.subscription_end_date = datetime.datetime.fromtimestamp(
                expiration_at_ms / 1000, tz=datetime.timezone.utc
            )
        logger.info("RevenueCat CANCELLATION: user %d cancelled", user.id)

    elif event_type == EVENT_EXPIRATION:
        user.subscription_status = "free"
        user.subscription_plan = "free"
        user.subscription_end_date = None
        logger.info("RevenueCat EXPIRATION: user %d reverted to free", user.id)

    elif event_type == EVENT_BILLING_ISSUE:
        user.subscription_status = "past_due"
        logger.warning("RevenueCat BILLING_ISSUE: user %d has billing issue", user.id)

    db.commit()
    return {"status": "ok"}
