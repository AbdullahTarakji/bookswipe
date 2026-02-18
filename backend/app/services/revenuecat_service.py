"""RevenueCat service for mobile in-app subscription management.

Handles server-side receipt validation via the RevenueCat REST API
and processes webhook events to sync subscription state with the database.
Stripe remains the billing provider for web-only users.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Any

import httpx

from app.config import settings
from app.exceptions import PaymentError

logger = logging.getLogger("bookswipe")

REVENUECAT_API_BASE = "https://api.revenuecat.com/v1"
PREMIUM_ENTITLEMENT = "premium"


# ── REST API helpers ─────────────────────────────────────────


def _headers() -> dict[str, str]:
    """Authorization headers for the RevenueCat REST API."""
    return {
        "Authorization": f"Bearer {settings.revenuecat_api_key}",
        "Content-Type": "application/json",
    }


async def get_subscriber(app_user_id: str) -> dict[str, Any]:
    """Fetch a subscriber record from RevenueCat.

    Returns the full subscriber object or raises PaymentError on failure.
    """
    url = f"{REVENUECAT_API_BASE}/subscribers/{app_user_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, headers=_headers())
    if resp.status_code == 404:
        raise PaymentError("Subscriber not found in RevenueCat")
    if resp.status_code != 200:
        logger.error("RevenueCat get_subscriber %s: %s", resp.status_code, resp.text)
        raise PaymentError("Failed to fetch subscriber from RevenueCat")
    return resp.json().get("subscriber", {})


async def check_premium_entitlement(app_user_id: str) -> bool:
    """Return True if the user currently has an active premium entitlement."""
    try:
        subscriber = await get_subscriber(app_user_id)
    except PaymentError:
        return False

    entitlements = subscriber.get("entitlements", {})
    premium = entitlements.get(PREMIUM_ENTITLEMENT)
    if not premium:
        return False
    # If expires_date is None the entitlement is lifetime; otherwise check
    # RevenueCat already filters out expired entitlements in active list
    return True


# ── Webhook verification ─────────────────────────────────────


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify the HMAC-SHA256 signature of a RevenueCat webhook payload.

    Returns False if the webhook secret is not configured or signature is invalid.
    """
    secret = settings.revenuecat_webhook_secret
    if not secret:
        logger.warning("RevenueCat webhook secret not configured — skipping verification")
        return True  # permissive in dev; enforce in production via config check
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Webhook event processing ─────────────────────────────────

# RevenueCat event types we care about
EVENT_INITIAL_PURCHASE = "INITIAL_PURCHASE"
EVENT_RENEWAL = "RENEWAL"
EVENT_CANCELLATION = "CANCELLATION"
EVENT_EXPIRATION = "EXPIRATION"
EVENT_BILLING_ISSUE = "BILLING_ISSUE"
EVENT_PRODUCT_CHANGE = "PRODUCT_CHANGE"
EVENT_SUBSCRIBER_ALIAS = "SUBSCRIBER_ALIAS"

HANDLED_EVENTS = {
    EVENT_INITIAL_PURCHASE,
    EVENT_RENEWAL,
    EVENT_CANCELLATION,
    EVENT_EXPIRATION,
    EVENT_BILLING_ISSUE,
    EVENT_PRODUCT_CHANGE,
}


def parse_webhook_event(body: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the relevant fields from a RevenueCat webhook payload.

    Returns a normalised dict with keys: event_type, app_user_id, product_id,
    expiration_at_ms, or None if the event should be ignored.
    """
    event = body.get("event", {})
    event_type = event.get("type")
    if event_type not in HANDLED_EVENTS:
        return None

    app_user_id = event.get("app_user_id")
    if not app_user_id:
        return None

    return {
        "event_type": event_type,
        "app_user_id": app_user_id,
        "product_id": event.get("product_id"),
        "expiration_at_ms": event.get("expiration_at_ms"),
        "store": event.get("store"),  # APP_STORE, PLAY_STORE, etc.
    }
