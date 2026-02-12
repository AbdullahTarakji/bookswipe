"""Tests for payment endpoints and swipe limits."""

import datetime
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import DailySwipeCount, User
from tests.conftest import VALID_TEST_PASSWORD, TestingSessionLocal


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def registered_user(client):
    resp = client.post("/api/auth/register", json={
        "email": "payment_test@example.com",
        "password": VALID_TEST_PASSWORD,
    })
    return resp.json()


@pytest.fixture()
def auth_headers(registered_user):
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest.fixture()
def premium_user(client, auth_headers):
    """Make the test user a premium subscriber."""
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "payment_test@example.com").first()
    user.subscription_status = "active"
    user.subscription_plan = "premium"
    user.stripe_customer_id = "cus_test_123"
    db.commit()
    db.close()
    return auth_headers


# --- Subscription Status ---

class TestSubscriptionEndpoints:
    def test_get_subscription_free_user(self, client, auth_headers):
        resp = client.get("/api/payments/subscription", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["subscription_status"] == "free"
        assert data["subscription_plan"] == "free"
        assert data["is_premium"] is False
        assert data["subscription_end_date"] is None

    def test_get_subscription_premium_user(self, client, premium_user):
        resp = client.get("/api/payments/subscription", headers=premium_user)
        assert resp.status_code == 200
        data = resp.json()
        assert data["subscription_status"] == "active"
        assert data["subscription_plan"] == "premium"
        assert data["is_premium"] is True

    def test_get_subscription_unauthenticated(self, client):
        resp = client.get("/api/payments/subscription")
        assert resp.status_code == 401


# --- Checkout ---

class TestCheckoutEndpoints:
    @patch("app.routers.payments.create_checkout_session")
    @patch("app.routers.payments.create_customer")
    def test_create_checkout_success(self, mock_create_customer, mock_create_session, client, auth_headers):
        mock_create_customer.return_value = "cus_new_123"
        mock_create_session.return_value = "https://checkout.stripe.com/session123"

        with patch("app.routers.payments.settings") as mock_settings:
            mock_settings.stripe_price_id = "price_test_123"
            mock_settings.free_tier_daily_swipe_limit = 10
            resp = client.post("/api/payments/create-checkout", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["checkout_url"] == "https://checkout.stripe.com/session123"

    def test_create_checkout_already_premium(self, client, premium_user):
        resp = client.post("/api/payments/create-checkout", headers=premium_user)
        assert resp.status_code == 400
        assert "already" in resp.json()["detail"].lower()

    def test_create_checkout_unauthenticated(self, client):
        resp = client.post("/api/payments/create-checkout")
        assert resp.status_code == 401


# --- Cancel Subscription ---

class TestCancelSubscription:
    @patch("app.routers.payments.cancel_subscription")
    @patch("app.routers.payments.stripe_lib.Subscription.list")
    def test_cancel_success(self, mock_sub_list, mock_cancel, client, premium_user):
        mock_sub = MagicMock()
        mock_sub.id = "sub_test_123"
        mock_sub_list.return_value = MagicMock(data=[mock_sub])

        resp = client.post("/api/payments/cancel", headers=premium_user)
        assert resp.status_code == 200
        assert "cancelled" in resp.json()["message"].lower()
        mock_cancel.assert_called_once_with("sub_test_123")

    def test_cancel_free_user(self, client, auth_headers):
        resp = client.post("/api/payments/cancel", headers=auth_headers)
        assert resp.status_code == 400


# --- Billing Portal ---

class TestBillingPortal:
    @patch("app.routers.payments.create_billing_portal_session")
    def test_portal_success(self, mock_portal, client, premium_user):
        mock_portal.return_value = "https://billing.stripe.com/portal123"
        resp = client.post("/api/payments/portal", headers=premium_user)
        assert resp.status_code == 200
        assert resp.json()["checkout_url"] == "https://billing.stripe.com/portal123"

    def test_portal_no_customer(self, client, auth_headers):
        resp = client.post("/api/payments/portal", headers=auth_headers)
        assert resp.status_code == 400


# --- Swipe Status ---

class TestSwipeStatus:
    def test_swipe_status_fresh_user(self, client, auth_headers):
        resp = client.get("/api/payments/swipe-status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["swipes_today"] == 0
        assert data["daily_limit"] == 10
        assert data["is_premium"] is False
        assert data["swipes_remaining"] == 10

    def test_swipe_status_premium_user(self, client, premium_user):
        resp = client.get("/api/payments/swipe-status", headers=premium_user)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_premium"] is True

    def test_swipe_status_after_swipes(self, client, auth_headers, mock_google_books_search):
        # Like a book to increment swipe count
        client.post("/api/books/like", json={
            "google_book_id": "test_swipe_book",
            "title": "Swipe Test",
            "authors": "Test",
            "thumbnail": "",
        }, headers=auth_headers)

        resp = client.get("/api/payments/swipe-status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["swipes_today"] == 1
        assert data["swipes_remaining"] == 9


# --- Swipe Limits on Like/Skip ---

class TestSwipeLimits:
    def test_free_user_can_swipe_within_limit(self, client, auth_headers, mock_google_books_search):
        resp = client.post("/api/books/like", json={
            "google_book_id": "limit_test_1",
            "title": "Test",
            "authors": "Author",
            "thumbnail": "",
        }, headers=auth_headers)
        assert resp.status_code == 201

    def test_free_user_blocked_at_limit(self, client, auth_headers):
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        db.add(DailySwipeCount(
            user_id=user.id,
            swipe_date=datetime.date.today(),
            count=10,
        ))
        db.commit()
        db.close()

        resp = client.post("/api/books/like", json={
            "google_book_id": "over_limit",
            "title": "Test",
            "authors": "Author",
            "thumbnail": "",
        }, headers=auth_headers)
        assert resp.status_code == 429
        assert "SWIPE_LIMIT_EXCEEDED" in resp.json()["error"]["code"]

    def test_premium_user_bypasses_limit(self, client, premium_user, mock_google_books_search):
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        db.add(DailySwipeCount(
            user_id=user.id,
            swipe_date=datetime.date.today(),
            count=100,
        ))
        db.commit()
        db.close()

        resp = client.post("/api/books/like", json={
            "google_book_id": "premium_unlimited",
            "title": "Premium Book",
            "authors": "Author",
            "thumbnail": "",
        }, headers=premium_user)
        assert resp.status_code == 201

    def test_skip_also_counts_swipe(self, client, auth_headers, mock_google_books_search):
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        db.add(DailySwipeCount(
            user_id=user.id,
            swipe_date=datetime.date.today(),
            count=10,
        ))
        db.commit()
        db.close()

        resp = client.post("/api/books/skip", json={
            "google_book_id": "skip_over_limit",
        }, headers=auth_headers)
        assert resp.status_code == 429


# --- Webhooks ---

class TestWebhooks:
    @patch("app.routers.payments.construct_webhook_event")
    def test_checkout_completed_webhook(self, mock_construct, client, auth_headers):
        # Set up user with stripe customer ID
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        user.stripe_customer_id = "cus_webhook_test"
        db.commit()
        db.close()

        mock_construct.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_webhook_test",
                }
            }
        }

        resp = client.post(
            "/api/payments/webhook",
            content=b"fake_payload",
            headers={"stripe-signature": "fake_sig"},
        )
        assert resp.status_code == 200

        # Verify user is now premium
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        assert user.subscription_status == "active"
        assert user.subscription_plan == "premium"
        db.close()

    @patch("app.routers.payments.construct_webhook_event")
    def test_subscription_deleted_webhook(self, mock_construct, client, premium_user):
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        customer_id = user.stripe_customer_id
        db.close()

        mock_construct.return_value = {
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "customer": customer_id,
                }
            }
        }

        resp = client.post(
            "/api/payments/webhook",
            content=b"fake_payload",
            headers={"stripe-signature": "fake_sig"},
        )
        assert resp.status_code == 200

        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        assert user.subscription_status == "free"
        assert user.subscription_plan == "free"
        db.close()

    @patch("app.routers.payments.construct_webhook_event")
    def test_payment_failed_webhook(self, mock_construct, client, premium_user):
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        customer_id = user.stripe_customer_id
        db.close()

        mock_construct.return_value = {
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "customer": customer_id,
                }
            }
        }

        resp = client.post(
            "/api/payments/webhook",
            content=b"fake_payload",
            headers={"stripe-signature": "fake_sig"},
        )
        assert resp.status_code == 200

        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        assert user.subscription_status == "past_due"
        db.close()

    @patch("app.routers.payments.construct_webhook_event")
    def test_subscription_updated_webhook(self, mock_construct, client, premium_user):
        db = TestingSessionLocal()
        user = db.query(User).filter(User.email == "payment_test@example.com").first()
        customer_id = user.stripe_customer_id
        db.close()

        mock_construct.return_value = {
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "customer": customer_id,
                    "status": "active",
                    "current_period_end": 1700000000,
                }
            }
        }

        resp = client.post(
            "/api/payments/webhook",
            content=b"fake_payload",
            headers={"stripe-signature": "fake_sig"},
        )
        assert resp.status_code == 200


# --- User Profile Shows Subscription ---

class TestUserProfileSubscription:
    def test_profile_includes_subscription_fields(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["subscription_status"] == "free"
        assert data["subscription_plan"] == "free"
        assert data["subscription_end_date"] is None

    def test_profile_premium_user(self, client, premium_user):
        resp = client.get("/api/auth/me", headers=premium_user)
        assert resp.status_code == 200
        data = resp.json()
        assert data["subscription_status"] == "active"
        assert data["subscription_plan"] == "premium"
