"""Tests for email service, email preferences, and email templates."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.email_service import (
    ConsoleBackend,
    EmailBackend,
    SMTPBackend,
    send_email,
    set_email_backend,
)
from app.services.email_templates import (
    render_recommendation_alert,
    render_weekly_digest,
    render_welcome,
)

from .conftest import VALID_TEST_PASSWORD


# ── Template Rendering Tests ─────────────────────────────────


class TestEmailTemplates:
    def test_render_welcome(self):
        subject, html = render_welcome("user@test.com")
        assert "Welcome" in subject
        assert "BookSwipe" in html
        assert "user@test.com" not in html  # no raw email leak
        assert "Start Swiping" in html

    def test_render_welcome_custom_url(self):
        subject, html = render_welcome("u@t.com", app_url="https://custom.app")
        assert "https://custom.app" in html

    def test_render_weekly_digest(self):
        stats = {"likes": 10, "skips": 5, "total_swipes": 15}
        recs = [{"title": "Book A", "authors": "Author A"}]
        popular = [{"title": "Book B", "authors": "Author B"}]
        subject, html = render_weekly_digest("u@t.com", stats, recs, popular)
        assert "Digest" in subject
        assert "10" in html  # likes count
        assert "Book A" in html
        assert "Book B" in html

    def test_render_weekly_digest_empty(self):
        stats = {"likes": 0, "skips": 0, "total_swipes": 0}
        subject, html = render_weekly_digest("u@t.com", stats, [], [])
        assert "Digest" in subject
        assert "0" in html

    def test_render_recommendation_alert(self):
        books = [
            {"title": "Cool Book", "authors": "Jane Doe"},
            {"title": "Another", "authors": "John"},
        ]
        subject, html = render_recommendation_alert(books)
        assert "matching" in subject.lower() or "New" in subject
        assert "Cool Book" in html
        assert "Jane Doe" in html

    def test_render_recommendation_alert_empty(self):
        subject, html = render_recommendation_alert([])
        assert subject  # still has a subject
        assert "html" in html.lower()

    def test_templates_are_mobile_friendly(self):
        """All templates should include viewport meta tag."""
        _, html = render_welcome("u@t.com")
        assert "viewport" in html
        _, html = render_weekly_digest("u@t.com", {"likes": 0, "skips": 0, "total_swipes": 0}, [], [])
        assert "viewport" in html
        _, html = render_recommendation_alert([])
        assert "viewport" in html


# ── Email Service Tests ──────────────────────────────────────


class MockBackend(EmailBackend):
    """Test backend that records calls."""

    def __init__(self):
        self.sent: list[tuple[str, str, str]] = []

    def send(self, to: str, subject: str, html_body: str) -> bool:
        self.sent.append((to, subject, html_body))
        return True


class TestEmailService:
    def test_send_email_uses_backend(self):
        mock = MockBackend()
        set_email_backend(mock)
        try:
            result = send_email("test@example.com", "Subject", "<p>Body</p>")
            assert result is True
            assert len(mock.sent) == 1
            assert mock.sent[0][0] == "test@example.com"
        finally:
            set_email_backend(ConsoleBackend())

    def test_console_backend(self):
        backend = ConsoleBackend()
        assert backend.send("a@b.com", "Hi", "<p>Hi</p>") is True

    def test_smtp_backend_no_host(self):
        backend = SMTPBackend(host="")
        assert backend.send("a@b.com", "Hi", "<p>Hi</p>") is False

    def test_smtp_backend_sends(self):
        with patch("app.services.email_service.smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            backend = SMTPBackend(
                host="smtp.test.com", port=587, user="u", password="p", from_email="f@t.com"
            )
            result = backend.send("to@test.com", "Subject", "<p>Body</p>")
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with("u", "p")
            mock_server.sendmail.assert_called_once()

    def test_smtp_backend_handles_exception(self):
        with patch("app.services.email_service.smtplib.SMTP", side_effect=Exception("conn failed")):
            backend = SMTPBackend(host="smtp.test.com")
            result = backend.send("to@test.com", "Subject", "<p>Body</p>")
            assert result is False

    def test_set_email_backend(self):
        mock = MockBackend()
        set_email_backend(mock)
        send_email("x@y.com", "s", "b")
        assert len(mock.sent) == 1
        set_email_backend(ConsoleBackend())


# ── Email Preference Endpoint Tests ──────────────────────────


class TestEmailPreferenceEndpoints:
    def test_get_email_preferences_defaults(self, client: TestClient, auth_headers: dict):
        resp = client.get("/api/notifications/email-preferences", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email_welcome"] is True
        assert data["email_weekly_digest"] is True
        assert data["email_recommendations"] is True

    def test_update_email_preferences(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            "/api/notifications/email-preferences",
            json={"email_weekly_digest": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email_weekly_digest"] is False
        assert data["email_welcome"] is True  # unchanged

    def test_update_email_preferences_all(self, client: TestClient, auth_headers: dict):
        resp = client.put(
            "/api/notifications/email-preferences",
            json={
                "email_welcome": False,
                "email_weekly_digest": False,
                "email_recommendations": False,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email_welcome"] is False
        assert data["email_weekly_digest"] is False
        assert data["email_recommendations"] is False

    def test_get_after_update_persists(self, client: TestClient, auth_headers: dict):
        client.put(
            "/api/notifications/email-preferences",
            json={"email_recommendations": False},
            headers=auth_headers,
        )
        resp = client.get("/api/notifications/email-preferences", headers=auth_headers)
        assert resp.json()["email_recommendations"] is False

    def test_unauthenticated_rejected(self, client: TestClient):
        resp = client.get("/api/notifications/email-preferences")
        assert resp.status_code in (401, 403)


# ── Welcome Email on Registration ────────────────────────────


class TestWelcomeEmail:
    def test_registration_sends_welcome_email(self, client: TestClient):
        mock = MockBackend()
        set_email_backend(mock)
        try:
            resp = client.post(
                "/api/auth/register",
                json={"email": "welcome@test.com", "password": VALID_TEST_PASSWORD},
            )
            assert resp.status_code == 201
            assert len(mock.sent) == 1
            assert mock.sent[0][0] == "welcome@test.com"
            assert "Welcome" in mock.sent[0][1]
        finally:
            set_email_backend(ConsoleBackend())

    def test_registration_succeeds_even_if_email_fails(self, client: TestClient):
        class FailBackend(EmailBackend):
            def send(self, to, subject, html_body):
                raise Exception("SMTP down")

        set_email_backend(FailBackend())
        try:
            resp = client.post(
                "/api/auth/register",
                json={"email": "fail@test.com", "password": VALID_TEST_PASSWORD},
            )
            assert resp.status_code == 201
        finally:
            set_email_backend(ConsoleBackend())
