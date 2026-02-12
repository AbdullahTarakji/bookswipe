"""Repository for admin-specific database operations."""

from __future__ import annotations

import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category, LikedBook, SkippedBook, User


class AdminRepository:
    """Encapsulates all database queries for admin operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        role: str | None = None,
        is_banned: bool | None = None,
    ) -> tuple[list[User], int]:
        """Return a paginated, optionally filtered list of users."""
        query = self.db.query(User)

        if search:
            query = query.filter(User.email.ilike(f"%{search}%"))
        if role:
            query = query.filter(User.role == role)
        if is_banned is not None:
            query = query.filter(User.is_banned == is_banned)

        total = query.count()
        users = (
            query.order_by(User.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return users, total

    def get_user_by_id(self, user_id: int) -> User | None:
        """Return a user by primary key (including inactive)."""
        return self.db.query(User).filter(User.id == user_id).first()

    def update_role(self, user: User, new_role: str) -> User:
        """Update a user's role."""
        user.role = new_role
        self.db.commit()
        self.db.refresh(user)
        return user

    def ban_user(self, user: User, reason: str | None = None) -> User:
        """Ban a user."""
        user.is_banned = True
        user.banned_at = datetime.datetime.now(datetime.timezone.utc)
        user.ban_reason = reason
        self.db.commit()
        self.db.refresh(user)
        return user

    def unban_user(self, user: User) -> User:
        """Unban a user."""
        user.is_banned = False
        user.banned_at = None
        user.ban_reason = None
        self.db.commit()
        self.db.refresh(user)
        return user

    def hard_delete_user(self, user: User) -> None:
        """Permanently delete a user and all associated data."""
        self.db.delete(user)
        self.db.commit()

    def get_total_users(self) -> int:
        """Return total user count."""
        return self.db.query(User).count()

    def get_active_users(self, since: datetime.datetime) -> int:
        """Return count of users created since the given datetime."""
        return self.db.query(User).filter(User.created_at >= since).count()

    def get_banned_users_count(self) -> int:
        """Return count of banned users."""
        return self.db.query(User).filter(User.is_banned.is_(True)).count()

    def get_admin_users_count(self) -> int:
        """Return count of admin users."""
        return self.db.query(User).filter(User.role == "admin").count()

    def get_total_likes(self) -> int:
        """Return total number of liked books."""
        return self.db.query(LikedBook).count()

    def get_total_skips(self) -> int:
        """Return total number of skipped books."""
        return self.db.query(SkippedBook).count()

    def get_counts_summary(self, active_since: datetime.datetime) -> dict:
        """Return all dashboard counts in 3 queries instead of 6.

        Batches the 4 User-table COUNTs into a single conditional-count query.
        """
        user_row = self.db.query(
            func.count(User.id).label("total"),
            func.count(User.id).filter(User.created_at >= active_since).label("active"),
            func.count(User.id).filter(User.is_banned.is_(True)).label("banned"),
            func.count(User.id).filter(User.role == "admin").label("admins"),
        ).one()

        total_likes = self.db.query(func.count(LikedBook.id)).scalar() or 0
        total_skips = self.db.query(func.count(SkippedBook.id)).scalar() or 0

        return {
            "total_users": user_row.total,
            "active_users": user_row.active,
            "banned_users": user_row.banned,
            "admin_users": user_row.admins,
            "total_likes": total_likes,
            "total_skips": total_skips,
        }

    def get_user_growth(self, days: int = 30) -> list[dict]:
        """Return daily user registration counts for the last N days."""
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
        rows = (
            self.db.query(
                func.date(User.created_at).label("date"),
                func.count(User.id).label("count"),
            )
            .filter(User.created_at >= cutoff)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at))
            .all()
        )
        return [{"date": str(row.date), "count": row.count} for row in rows]

    def get_popular_categories(self, limit: int = 10) -> list[dict]:
        """Return categories with the total number of liked books.

        NOTE: LikedBook has no category column, so we cannot map individual
        likes to categories.  We return each category alongside the global
        like count so the admin dashboard has *something* to show.  To get
        real per-category stats, add a ``category`` column to LikedBook and
        populate it at like-time from the Google Books metadata.
        """
        categories = self.db.query(Category).limit(limit).all()
        total_likes = self.get_total_likes()
        return [{"name": cat.name, "total_likes": total_likes} for cat in categories]

    def get_recent_users(self, limit: int = 5) -> list[User]:
        """Return the most recently registered users."""
        return (
            self.db.query(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )
