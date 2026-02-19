"""Payments router: Stripe checkout (web), RevenueCat (mobile), webhooks, and subscription management.

Platform routing:
- Web clients use Stripe checkout sessions and billing portal.
- Mobile clients (iOS/Android) use RevenueCat for in-app purchases;
  subscription state is synced via RevenueCat webhooks.
"""

import datetime
import logging

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.exceptions import PaymentError
from app.models import DailySwipeCount, User
from app.schemas import (
    CheckoutSessionResponse,
    MessageResponse,
    SubscriptionResponse,
    SwipeLimitResponse,
)
from app.services.auth import get_current_user
import stripe as stripe_lib
from app.services.stripe_service import (
    cancel_subscription,
    construct_webhook_event,
    create_billing_portal_session,
    create_checkout_session,
    create_customer,
)

logger = logging.getLogger("bookswipe")
router = APIRouter(prefix="/api/payments", tags=["payments"])


def _ensure_stripe_customer(user: User, db: Session) -> str:
    """Ensure the user has a Stripe customer ID, creating one if needed."""
    if user.stripe_customer_id:
        return user.stripe_customer_id
    customer_id = create_customer(user.email)
    user.stripe_customer_id = customer_id
    db.commit()
    return customer_id


@router.post("/create-checkout", response_model=CheckoutSessionResponse)
def create_checkout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_platform: str = Header(default="web", alias="X-Platform"),
):
    """Create a Stripe checkout session for Premium subscription (web only).

    Mobile clients should use RevenueCat SDK directly for purchases;
    this endpoint is only for web-based Stripe checkout.
    """
    if x_platform in ("ios", "android"):
        raise PaymentError(
            "Mobile subscriptions are handled via in-app purchase. "
            "Use the RevenueCat SDK in the app."
        )
    if current_user.is_premium:
        raise PaymentError("You already have an active Premium subscription")
    if not settings.stripe_price_id:
        raise PaymentError("Stripe is not configured")
    customer_id = _ensure_stripe_customer(current_user, db)
    checkout_url = create_checkout_session(customer_id, settings.stripe_price_id)
    return CheckoutSessionResponse(checkout_url=checkout_url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    event = construct_webhook_event(payload, sig_header)

    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        _handle_checkout_completed(data_object, db)
    elif event_type == "customer.subscription.updated":
        _handle_subscription_updated(data_object, db)
    elif event_type == "customer.subscription.deleted":
        _handle_subscription_deleted(data_object, db)
    elif event_type == "invoice.payment_failed":
        _handle_payment_failed(data_object, db)

    return {"status": "ok"}


@router.get("/subscription", response_model=SubscriptionResponse)
def get_subscription(current_user: User = Depends(get_current_user)):
    """Get the current user's subscription status."""
    return SubscriptionResponse(
        subscription_status=current_user.subscription_status,
        subscription_plan=current_user.subscription_plan,
        subscription_end_date=current_user.subscription_end_date,
        is_premium=current_user.is_premium,
    )


@router.post("/cancel", response_model=MessageResponse)
def cancel_subscription_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel the current user's subscription at period end."""
    if not current_user.is_premium:
        raise PaymentError("No active subscription to cancel")
    if not current_user.stripe_customer_id:
        raise PaymentError("No payment profile found")

    subscriptions = stripe_lib.Subscription.list(
        customer=current_user.stripe_customer_id, status="active", limit=1
    )
    if not subscriptions.data:
        raise PaymentError("No active subscription found")

    cancel_subscription(subscriptions.data[0].id)

    current_user.subscription_status = "cancelled"
    db.commit()
    return MessageResponse(message="Subscription will be cancelled at end of billing period")


@router.post("/portal", response_model=CheckoutSessionResponse)
def billing_portal(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe billing portal session."""
    if not current_user.stripe_customer_id:
        raise PaymentError("No payment profile found")
    portal_url = create_billing_portal_session(current_user.stripe_customer_id)
    return CheckoutSessionResponse(checkout_url=portal_url)


@router.get("/swipe-status", response_model=SwipeLimitResponse)
def get_swipe_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's swipe limit status for today."""
    today = datetime.date.today()
    record = (
        db.query(DailySwipeCount)
        .filter(DailySwipeCount.user_id == current_user.id, DailySwipeCount.swipe_date == today)
        .first()
    )
    swipes_today = record.count if record else 0
    daily_limit = settings.free_tier_daily_swipe_limit
    is_premium = current_user.is_premium

    return SwipeLimitResponse(
        swipes_today=swipes_today,
        daily_limit=daily_limit,
        is_premium=is_premium,
        swipes_remaining=max(0, daily_limit - swipes_today) if not is_premium else daily_limit,
    )


# --- Webhook Handlers ---

def _find_user_by_stripe_customer(customer_id: str, db: Session) -> User | None:
    """Look up a user by their Stripe customer ID."""
    return db.query(User).filter(User.stripe_customer_id == customer_id).first()


def _handle_checkout_completed(data: dict, db: Session) -> None:
    """Handle checkout.session.completed: activate subscription."""
    customer_id = data.get("customer")
    if not customer_id:
        return
    user = _find_user_by_stripe_customer(customer_id, db)
    if not user:
        logger.warning("Webhook: no user for customer %s", customer_id)
        return
    user.subscription_status = "active"
    user.subscription_plan = "premium"
    db.commit()
    logger.info("Subscription activated for user %d", user.id)


def _handle_subscription_updated(data: dict, db: Session) -> None:
    """Handle customer.subscription.updated: sync status."""
    customer_id = data.get("customer")
    if not customer_id:
        return
    user = _find_user_by_stripe_customer(customer_id, db)
    if not user:
        return

    status = data.get("status", "")
    if status == "active":
        user.subscription_status = "active"
        user.subscription_plan = "premium"
    elif status in ("past_due", "unpaid"):
        user.subscription_status = "past_due"
    elif status == "canceled":
        user.subscription_status = "free"
        user.subscription_plan = "free"

    current_period_end = data.get("current_period_end")
    if current_period_end:
        user.subscription_end_date = datetime.datetime.fromtimestamp(
            current_period_end, tz=datetime.timezone.utc
        )
    db.commit()


def _handle_subscription_deleted(data: dict, db: Session) -> None:
    """Handle customer.subscription.deleted: revert to free."""
    customer_id = data.get("customer")
    if not customer_id:
        return
    user = _find_user_by_stripe_customer(customer_id, db)
    if not user:
        return
    user.subscription_status = "free"
    user.subscription_plan = "free"
    user.subscription_end_date = None
    db.commit()
    logger.info("Subscription deleted for user %d", user.id)


def _handle_payment_failed(data: dict, db: Session) -> None:
    """Handle invoice.payment_failed: mark as past_due."""
    customer_id = data.get("customer")
    if not customer_id:
        return
    user = _find_user_by_stripe_customer(customer_id, db)
    if not user:
        return
    user.subscription_status = "past_due"
    db.commit()
    logger.warning("Payment failed for user %d", user.id)
