"""Tests for notification endpoints: device token management, preferences, and history."""

from unittest.mock import patch

import pytest

from app.models import User
from app.services.auth import create_access_token, hash_password
from tests.conftest import VALID_TEST_PASSWORD


@pytest.fixture()
def user_and_headers(db_session):
    """Create a regular user and return (user, auth_headers)."""
    user = User(
        email="notif@test.com",
        hashed_password=hash_password(VALID_TEST_PASSWORD),
        role="user",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(user.id)
    return user, {"Authorization": f"Bearer {token}"}


class TestRegisterDevice:
    """Tests for POST /api/notifications/register-device."""

    def test_register_device_success(self, client, user_and_headers):
        _, headers = user_and_headers
        resp = client.post("/api/notifications/register-device", json={
            "token": "fcm_token_abc123",
            "platform": "android",
        }, headers=headers)
        assert resp.status_code == 201
        assert resp.json()["message"] == "Device registered successfully"

    def test_register_device_duplicate(self, client, user_and_headers):
        _, headers = user_and_headers
        body = {"token": "fcm_token_dup", "platform": "ios"}
        resp1 = client.post("/api/notifications/register-device", json=body, headers=headers)
        assert resp1.status_code == 201
        resp2 = client.post("/api/notifications/register-device", json=body, headers=headers)
        assert resp2.status_code == 201

    def test_register_device_invalid_platform(self, client, user_and_headers):
        _, headers = user_and_headers
        resp = client.post("/api/notifications/register-device", json={
            "token": "fcm_token_x",
            "platform": "windows",
        }, headers=headers)
        assert resp.status_code == 422

    def test_register_device_unauthenticated(self, client):
        resp = client.post("/api/notifications/register-device", json={
            "token": "fcm_token_x",
            "platform": "android",
        })
        assert resp.status_code == 401


class TestUnregisterDevice:
    """Tests for POST /api/notifications/unregister-device."""

    def test_unregister_device_success(self, client, user_and_headers):
        _, headers = user_and_headers
        client.post("/api/notifications/register-device", json={
            "token": "fcm_token_remove",
            "platform": "android",
        }, headers=headers)
        resp = client.post("/api/notifications/unregister-device", json={
            "token": "fcm_token_remove",
        }, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["message"] == "Device unregistered successfully"

    def test_unregister_nonexistent_token(self, client, user_and_headers):
        _, headers = user_and_headers
        resp = client.post("/api/notifications/unregister-device", json={
            "token": "nonexistent_token",
        }, headers=headers)
        assert resp.status_code == 200


class TestNotificationPreferences:
    """Tests for GET/PUT /api/notifications/preferences."""

    def test_get_default_preferences(self, client, user_and_headers):
        _, headers = user_and_headers
        resp = client.get("/api/notifications/preferences", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["recommendations"] is True
        assert data["social"] is True
        assert data["marketing"] is False

    def test_update_preferences(self, client, user_and_headers):
        _, headers = user_and_headers
        resp = client.put("/api/notifications/preferences", json={
            "recommendations": False,
            "marketing": True,
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["recommendations"] is False
        assert data["social"] is True
        assert data["marketing"] is True

    def test_update_partial_preferences(self, client, user_and_headers):
        _, headers = user_and_headers
        # First set all
        client.put("/api/notifications/preferences", json={
            "recommendations": False,
            "social": False,
            "marketing": True,
        }, headers=headers)
        # Then update only one
        resp = client.put("/api/notifications/preferences", json={
            "social": True,
        }, headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["recommendations"] is False
        assert data["social"] is True
        assert data["marketing"] is True

    def test_preferences_unauthenticated(self, client):
        resp = client.get("/api/notifications/preferences")
        assert resp.status_code == 401


class TestNotificationHistory:
    """Tests for GET /api/notifications/history and mark-read endpoints."""

    def test_empty_history(self, client, user_and_headers):
        _, headers = user_and_headers
        resp = client.get("/api/notifications/history", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["notifications"] == []
        assert data["total"] == 0
        assert data["unread_count"] == 0

    def test_history_with_notifications(self, client, user_and_headers, db_session):
        user, headers = user_and_headers
        from app.repositories.notification_repository import NotificationRepository
        repo = NotificationRepository(db_session)
        repo.create_notification(user.id, "Title 1", "Body 1", category="recommendations")
        repo.create_notification(user.id, "Title 2", "Body 2", category="social", deep_link="/book/123")

        resp = client.get("/api/notifications/history", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["unread_count"] == 2
        assert len(data["notifications"]) == 2

    def test_mark_notification_read(self, client, user_and_headers, db_session):
        user, headers = user_and_headers
        from app.repositories.notification_repository import NotificationRepository
        repo = NotificationRepository(db_session)
        notif = repo.create_notification(user.id, "Title", "Body")

        resp = client.post(f"/api/notifications/history/{notif.id}/read", headers=headers)
        assert resp.status_code == 200

        # Verify it's marked as read
        history = client.get("/api/notifications/history", headers=headers)
        assert history.json()["unread_count"] == 0

    def test_mark_all_read(self, client, user_and_headers, db_session):
        user, headers = user_and_headers
        from app.repositories.notification_repository import NotificationRepository
        repo = NotificationRepository(db_session)
        repo.create_notification(user.id, "T1", "B1")
        repo.create_notification(user.id, "T2", "B2")
        repo.create_notification(user.id, "T3", "B3")

        resp = client.post("/api/notifications/history/read-all", headers=headers)
        assert resp.status_code == 200
        assert "3" in resp.json()["message"]

        history = client.get("/api/notifications/history", headers=headers)
        assert history.json()["unread_count"] == 0

    def test_history_pagination(self, client, user_and_headers, db_session):
        user, headers = user_and_headers
        from app.repositories.notification_repository import NotificationRepository
        repo = NotificationRepository(db_session)
        for i in range(5):
            repo.create_notification(user.id, f"Title {i}", f"Body {i}")

        resp = client.get("/api/notifications/history?page=1&page_size=2", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["notifications"]) == 2
        assert data["total"] == 5

    def test_history_unauthenticated(self, client):
        resp = client.get("/api/notifications/history")
        assert resp.status_code == 401


class TestNotificationService:
    """Tests for the notification service layer."""

    def test_notify_user_respects_preferences(self, db_session, user_and_headers):
        user, _ = user_and_headers
        from app.repositories.notification_repository import NotificationRepository
        from app.services.notification import notify_user

        # Disable recommendations
        repo = NotificationRepository(db_session)
        repo.upsert_preferences(user.id, recommendations=False)

        with patch("app.services.notification.send_push") as mock_push:
            # Register a device
            repo.register_device_token(user.id, "test_token", "android")
            notify_user(db_session, user.id, "Test", "Body", category="recommendations")
            # Push should NOT be called because recommendations are disabled
            mock_push.assert_not_called()

    def test_notify_user_sends_push_when_allowed(self, db_session, user_and_headers):
        user, _ = user_and_headers
        from app.repositories.notification_repository import NotificationRepository
        from app.services.notification import notify_user

        repo = NotificationRepository(db_session)
        repo.register_device_token(user.id, "test_token", "android")
        repo.upsert_preferences(user.id, social=True)

        with patch("app.services.notification.send_push") as mock_push:
            notify_user(db_session, user.id, "Test", "Body", category="social")
            mock_push.assert_called_once()

    def test_render_template(self):
        from app.services.notification import render_template

        result = render_template(
            "friend_activity",
            friend_name="Alice",
            book_title="The Hobbit",
            book_id="abc123",
        )
        assert result["title"] == "Your friend is reading"
        assert "Alice" in result["body"]
        assert "The Hobbit" in result["body"]
        assert result["category"] == "social"
        assert "abc123" in result["deep_link"]

    def test_render_template_unknown_key(self):
        from app.services.notification import render_template

        with pytest.raises(KeyError):
            render_template("nonexistent_template")
