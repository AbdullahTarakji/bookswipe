"""Tests for RevenueCat webhook handler and service."""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
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

from .conftest import VALID_TEST_PASSWORD, TestingSessionLocal

client = TestClient(app)


# ── Helper ───────────────────────────────────────────────────

def _register_user(email: str = "rc@test.com") -> dict:
    """Register a user and return dict with 'access_token' and 'user_id'."""
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": VALID_TEST_PASSWORD,
    })
    assert resp.status_code == 201
    data = resp.json()
    # Look up the user ID from the database
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    data["id"] = user.id
    db.close()
    return data


def _make_webhook_payload(event_type: str, app_user_id: str, **kwargs) -> dict:
    """Build a minimal RevenueCat webhook payload."""
    event = {
        "type": event_type,
        "app_user_id": app_user_id,
        "product_id": kwargs.get("product_id", "premium_monthly"),
        "expiration_at_ms": kwargs.get("expiration_at_ms"),
        "store": kwargs.get("store", "APP_STORE"),
    }
    return {"event": event}


def _sign_payload(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for a payload."""
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


# ── Unit tests: parse_webhook_event ──────────────────────────

class TestParseWebhookEvent:
    def test_initial_purchase(self):
        body = _make_webhook_payload(EVENT_INITIAL_PURCHASE, "42", expiration_at_ms=1700000000000)
        result = parse_webhook_event(body)
        assert result is not None
        assert result["event_type"] == EVENT_INITIAL_PURCHASE
        assert result["app_user_id"] == "42"
        assert result["expiration_at_ms"] == 1700000000000

    def test_unknown_event_ignored(self):
        body = _make_webhook_payload("UNKNOWN_EVENT", "42")
        assert parse_webhook_event(body) is None

    def test_missing_app_user_id(self):
        body = {"event": {"type": EVENT_INITIAL_PURCHASE}}
        assert parse_webhook_event(body) is None

    def test_cancellation(self):
        body = _make_webhook_payload(EVENT_CANCELLATION, "10")
        result = parse_webhook_event(body)
        assert result["event_type"] == EVENT_CANCELLATION

    def test_expiration(self):
        body = _make_webhook_payload(EVENT_EXPIRATION, "10")
        result = parse_webhook_event(body)
        assert result["event_type"] == EVENT_EXPIRATION

    def test_billing_issue(self):
        body = _make_webhook_payload(EVENT_BILLING_ISSUE, "10")
        result = parse_webhook_event(body)
        assert result["event_type"] == EVENT_BILLING_ISSUE

    def test_renewal(self):
        body = _make_webhook_payload(EVENT_RENEWAL, "10", expiration_at_ms=1800000000000)
        result = parse_webhook_event(body)
        assert result["event_type"] == EVENT_RENEWAL
        assert result["expiration_at_ms"] == 1800000000000


# ── Unit tests: verify_webhook_signature ─────────────────────

class TestVerifyWebhookSignature:
    def test_valid_signature(self):
        with patch.object(settings, "revenuecat_webhook_secret", "test-secret"):
            payload = b'{"event": {}}'
            sig = _sign_payload(payload, "test-secret")
            assert verify_webhook_signature(payload, sig) is True

    def test_invalid_signature(self):
        with patch.object(settings, "revenuecat_webhook_secret", "test-secret"):
            payload = b'{"event": {}}'
            assert verify_webhook_signature(payload, "bad-sig") is False

    def test_no_secret_configured(self):
        with patch.object(settings, "revenuecat_webhook_secret", ""):
            assert verify_webhook_signature(b"anything", "") is True


# ── Integration tests: webhook endpoint ──────────────────────

class TestRevenueCatWebhookEndpoint:
    def _post_webhook(self, payload: dict, secret: str = "") -> "Response":
        body = json.dumps(payload).encode()
        headers = {}
        if secret:
            headers["X-RevenueCat-Signature"] = _sign_payload(body, secret)
        return client.post(
            "/api/webhooks/revenuecat",
            content=body,
            headers={**headers, "Content-Type": "application/json"},
        )

    def test_initial_purchase_activates_premium(self):
        user_data = _register_user("rc_purchase@test.com")
        user_id = str(user_data["id"])

        with patch.object(settings, "revenuecat_webhook_secret", ""):
            payload = _make_webhook_payload(
                EVENT_INITIAL_PURCHASE, user_id, expiration_at_ms=1700000000000
            )
            resp = self._post_webhook(payload)
            assert resp.status_code == 200
            assert resp.json()["status"] == "ok"

        # Verify subscription is active
        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == int(user_id)).first()
        assert user.subscription_status == "active"
        assert user.subscription_plan == "premium"
        assert user.subscription_end_date is not None
        db.close()

    def test_cancellation_updates_status(self):
        user_data = _register_user("rc_cancel@test.com")
        user_id = str(user_data["id"])

        with patch.object(settings, "revenuecat_webhook_secret", ""):
            # First activate
            self._post_webhook(_make_webhook_payload(EVENT_INITIAL_PURCHASE, user_id))
            # Then cancel
            resp = self._post_webhook(_make_webhook_payload(EVENT_CANCELLATION, user_id))
            assert resp.status_code == 200

        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == int(user_id)).first()
        assert user.subscription_status == "cancelled"
        db.close()

    def test_expiration_reverts_to_free(self):
        user_data = _register_user("rc_expire@test.com")
        user_id = str(user_data["id"])

        with patch.object(settings, "revenuecat_webhook_secret", ""):
            self._post_webhook(_make_webhook_payload(EVENT_INITIAL_PURCHASE, user_id))
            resp = self._post_webhook(_make_webhook_payload(EVENT_EXPIRATION, user_id))
            assert resp.status_code == 200

        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == int(user_id)).first()
        assert user.subscription_status == "free"
        assert user.subscription_plan == "free"
        db.close()

    def test_billing_issue_marks_past_due(self):
        user_data = _register_user("rc_billing@test.com")
        user_id = str(user_data["id"])

        with patch.object(settings, "revenuecat_webhook_secret", ""):
            self._post_webhook(_make_webhook_payload(EVENT_INITIAL_PURCHASE, user_id))
            resp = self._post_webhook(_make_webhook_payload(EVENT_BILLING_ISSUE, user_id))
            assert resp.status_code == 200

        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == int(user_id)).first()
        assert user.subscription_status == "past_due"
        db.close()

    def test_unknown_user_returns_user_not_found(self):
        with patch.object(settings, "revenuecat_webhook_secret", ""):
            payload = _make_webhook_payload(EVENT_INITIAL_PURCHASE, "99999")
            resp = self._post_webhook(payload)
            assert resp.status_code == 200
            assert resp.json()["status"] == "user_not_found"

    def test_ignored_event(self):
        with patch.object(settings, "revenuecat_webhook_secret", ""):
            payload = _make_webhook_payload("TEST", "1")
            resp = self._post_webhook(payload)
            assert resp.status_code == 200
            assert resp.json()["status"] == "ignored"

    def test_invalid_signature_rejected(self):
        with patch.object(settings, "revenuecat_webhook_secret", "real-secret"):
            payload = _make_webhook_payload(EVENT_INITIAL_PURCHASE, "1")
            body = json.dumps(payload).encode()
            resp = client.post(
                "/api/webhooks/revenuecat",
                content=body,
                headers={
                    "X-RevenueCat-Signature": "invalid",
                    "Content-Type": "application/json",
                },
            )
            assert resp.status_code == 400

    def test_renewal_updates_subscription(self):
        user_data = _register_user("rc_renew@test.com")
        user_id = str(user_data["id"])

        with patch.object(settings, "revenuecat_webhook_secret", ""):
            self._post_webhook(_make_webhook_payload(EVENT_INITIAL_PURCHASE, user_id))
            resp = self._post_webhook(
                _make_webhook_payload(EVENT_RENEWAL, user_id, expiration_at_ms=1800000000000)
            )
            assert resp.status_code == 200

        db = TestingSessionLocal()
        user = db.query(User).filter(User.id == int(user_id)).first()
        assert user.subscription_status == "active"
        assert user.subscription_plan == "premium"
        db.close()


class TestPaymentsRouterPlatformDetection:
    """Test that mobile platforms are rejected from Stripe checkout."""

    def test_mobile_checkout_rejected(self):
        user_data = _register_user("mobile@test.com")
        token = user_data["access_token"]
        resp = client.post(
            "/api/payments/create-checkout",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Platform": "ios",
            },
        )
        assert resp.status_code == 400
        assert "in-app purchase" in resp.json()["detail"].lower()

    def test_android_checkout_rejected(self):
        user_data = _register_user("android@test.com")
        token = user_data["access_token"]
        resp = client.post(
            "/api/payments/create-checkout",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Platform": "android",
            },
        )
        assert resp.status_code == 400
