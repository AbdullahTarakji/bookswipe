"""Repository for notification-related database operations."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import DeviceToken, Notification, NotificationPreference


class NotificationRepository:
    """Encapsulates database queries for device tokens, preferences, and notifications."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Device Tokens ────────────────────────────────────────

    def register_device_token(self, user_id: int, token: str, platform: str) -> DeviceToken:
        """Store a device token, ignoring duplicates."""
        existing = (
            self.db.query(DeviceToken)
            .filter(DeviceToken.user_id == user_id, DeviceToken.token == token)
            .first()
        )
        if existing:
            return existing
        device = DeviceToken(user_id=user_id, token=token, platform=platform)
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def unregister_device_token(self, user_id: int, token: str) -> bool:
        """Remove a device token. Returns True if a token was deleted."""
        count = (
            self.db.query(DeviceToken)
            .filter(DeviceToken.user_id == user_id, DeviceToken.token == token)
            .delete()
        )
        self.db.commit()
        return count > 0

    def get_device_tokens(self, user_id: int) -> list[DeviceToken]:
        """Return all device tokens for a user."""
        return self.db.query(DeviceToken).filter(DeviceToken.user_id == user_id).all()

    # ── Notification Preferences ─────────────────────────────

    def get_preferences(self, user_id: int) -> NotificationPreference | None:
        """Return notification preferences for a user, or None if unset."""
        return (
            self.db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .first()
        )

    def upsert_preferences(
        self,
        user_id: int,
        *,
        recommendations: bool | None = None,
        social: bool | None = None,
        marketing: bool | None = None,
    ) -> NotificationPreference:
        """Create or update notification preferences for a user."""
        pref = self.get_preferences(user_id)
        if pref is None:
            pref = NotificationPreference(
                user_id=user_id,
                recommendations=recommendations if recommendations is not None else True,
                social=social if social is not None else True,
                marketing=marketing if marketing is not None else False,
            )
            self.db.add(pref)
        else:
            if recommendations is not None:
                pref.recommendations = recommendations
            if social is not None:
                pref.social = social
            if marketing is not None:
                pref.marketing = marketing
        self.db.commit()
        self.db.refresh(pref)
        return pref

    # ── Email Preferences ─────────────────────────────────────

    def get_email_preferences(self, user_id: int) -> NotificationPreference | None:
        """Return email preferences (same row as push prefs)."""
        return self.get_preferences(user_id)

    def upsert_email_preferences(
        self,
        user_id: int,
        *,
        email_welcome: bool | None = None,
        email_weekly_digest: bool | None = None,
        email_recommendations: bool | None = None,
    ) -> NotificationPreference:
        """Create or update email notification preferences."""
        pref = self.get_preferences(user_id)
        if pref is None:
            pref = NotificationPreference(
                user_id=user_id,
                email_welcome=email_welcome if email_welcome is not None else True,
                email_weekly_digest=email_weekly_digest if email_weekly_digest is not None else True,
                email_recommendations=email_recommendations if email_recommendations is not None else True,
            )
            self.db.add(pref)
        else:
            if email_welcome is not None:
                pref.email_welcome = email_welcome
            if email_weekly_digest is not None:
                pref.email_weekly_digest = email_weekly_digest
            if email_recommendations is not None:
                pref.email_recommendations = email_recommendations
        self.db.commit()
        self.db.refresh(pref)
        return pref

    # ── Notifications (History) ──────────────────────────────

    def create_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        category: str = "general",
        deep_link: str | None = None,
    ) -> Notification:
        """Create a notification record in the user's history."""
        notif = Notification(
            user_id=user_id,
            title=title,
            body=body,
            category=category,
            deep_link=deep_link,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def get_notifications(
        self, user_id: int, page: int = 1, page_size: int = 20
    ) -> tuple[list[Notification], int]:
        """Return paginated notifications for a user, newest first."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        total = query.count()
        notifications = (
            query.order_by(Notification.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return notifications, total

    def get_unread_count(self, user_id: int) -> int:
        """Return the number of unread notifications for a user."""
        return (
            self.db.query(func.count(Notification.id))
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .scalar()
            or 0
        )

    def mark_as_read(self, user_id: int, notification_id: int) -> bool:
        """Mark a single notification as read. Returns True if updated."""
        count = (
            self.db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .update({"is_read": True})
        )
        self.db.commit()
        return count > 0

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user. Returns the number updated."""
        count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .update({"is_read": True})
        )
        self.db.commit()
        return count
