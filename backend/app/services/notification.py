"""Notification service: FCM push delivery, templates, and history management."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Notification
from app.repositories.notification_repository import NotificationRepository

logger = logging.getLogger("bookswipe")

# ── FCM Initialisation ───────────────────────────────────────

_fcm_app: Any = None


def _get_fcm_app() -> Any:
    """Lazily initialise the Firebase Admin SDK.

    Returns the firebase_admin App instance, or None if credentials
    are not configured (e.g. in development / tests).
    """
    global _fcm_app
    if _fcm_app is not None:
        return _fcm_app

    if not settings.fcm_credentials_path:
        logger.info("FCM credentials not configured — push notifications disabled")
        return None

    try:
        import firebase_admin  # type: ignore[import-untyped]
        from firebase_admin import credentials  # type: ignore[import-untyped]

        cred = credentials.Certificate(settings.fcm_credentials_path)
        _fcm_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialised")
        return _fcm_app
    except Exception:
        logger.exception("Failed to initialise Firebase Admin SDK")
        return None


# ── Notification Templates ───────────────────────────────────


TEMPLATES: dict[str, dict[str, str]] = {
    "new_recommendations": {
        "title": "Fresh picks for you!",
        "body": "We found new book recommendations based on your taste. Swipe now!",
        "category": "recommendations",
        "deep_link": "/",
    },
    "friend_activity": {
        "title": "Your friend is reading",
        "body": "{friend_name} just liked \"{book_title}\". Check it out!",
        "category": "social",
        "deep_link": "/book/{book_id}",
    },
    "book_club_update": {
        "title": "Book club update",
        "body": "New activity in your book club: {club_name}",
        "category": "social",
        "deep_link": "/",
    },
}


def render_template(template_key: str, **kwargs: str) -> dict[str, str]:
    """Render a notification template with variable substitution.

    Returns a dict with keys: title, body, category, deep_link.
    Raises KeyError if the template_key is unknown.
    """
    tmpl = TEMPLATES[template_key]
    return {
        "title": tmpl["title"].format(**kwargs),
        "body": tmpl["body"].format(**kwargs),
        "category": tmpl["category"],
        "deep_link": tmpl["deep_link"].format(**kwargs),
    }


# ── Push Delivery ────────────────────────────────────────────


def send_push(token: str, title: str, body: str, data: dict[str, str] | None = None) -> bool:
    """Send a push notification to a single device via FCM.

    Returns True if the message was sent successfully, False otherwise.
    """
    app = _get_fcm_app()
    if app is None:
        logger.debug("FCM not initialised — skipping push to token=%s...", token[:8])
        return False

    try:
        from firebase_admin import messaging  # type: ignore[import-untyped]

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            token=token,
        )
        messaging.send(message)
        return True
    except Exception:
        logger.exception("Failed to send FCM push to token=%s...", token[:8])
        return False


# ── High-level Helpers ───────────────────────────────────────


def notify_user(
    db: Session,
    user_id: int,
    title: str,
    body: str,
    category: str = "general",
    deep_link: str | None = None,
    data: dict[str, str] | None = None,
) -> Notification:
    """Store a notification and send pushes to all user devices.

    Respects the user's notification preference for the given category.
    Returns the created Notification record.
    """
    repo = NotificationRepository(db)

    # Check preferences
    prefs = repo.get_preferences(user_id)
    category_allowed = True
    if prefs is not None:
        pref_map = {
            "recommendations": prefs.recommendations,
            "social": prefs.social,
            "marketing": prefs.marketing,
        }
        category_allowed = pref_map.get(category, True)

    # Always store in history, but only push if allowed
    notif = repo.create_notification(
        user_id=user_id,
        title=title,
        body=body,
        category=category,
        deep_link=deep_link,
    )

    if category_allowed:
        tokens = repo.get_device_tokens(user_id)
        push_data = {"deep_link": deep_link or "", "notification_id": str(notif.id)}
        if data:
            push_data.update(data)
        for dt in tokens:
            send_push(dt.token, title, body, data=push_data)

    return notif


def notify_user_from_template(
    db: Session,
    user_id: int,
    template_key: str,
    **kwargs: str,
) -> Notification:
    """Render a template and send a notification to the user.

    See TEMPLATES for available template keys and their required variables.
    """
    rendered = render_template(template_key, **kwargs)
    return notify_user(
        db,
        user_id=user_id,
        title=rendered["title"],
        body=rendered["body"],
        category=rendered["category"],
        deep_link=rendered["deep_link"],
    )
