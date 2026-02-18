"""SQLAlchemy ORM models for the BookSwipe database schema."""

from __future__ import annotations

import datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """Application user account with support for email and OAuth authentication."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False, default="email", server_default="email")
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user", server_default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default="1")
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="0")
    banned_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    ban_reason: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    deleted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True, default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Stripe subscription fields
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None, index=True)
    subscription_status: Mapped[str] = mapped_column(String(20), nullable=False, default="free", server_default="free")
    subscription_plan: Mapped[str] = mapped_column(String(20), nullable=False, default="free", server_default="free")
    subscription_end_date: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True, default=None)

    liked_books: Mapped[list[LikedBook]] = relationship(back_populates="user", cascade="all, delete-orphan")
    skipped_books: Mapped[list[SkippedBook]] = relationship(back_populates="user", cascade="all, delete-orphan")
    swipe_events: Mapped[list[SwipeEvent]] = relationship(back_populates="user", cascade="all, delete-orphan")
    preferences: Mapped[UserPreference | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    device_tokens: Mapped[list[DeviceToken]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notification_preference: Mapped[NotificationPreference | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    notifications: Mapped[list[Notification]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # Social features
    profile: Mapped[UserProfile | None] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    book_lists: Mapped[list[BookList]] = relationship(back_populates="user", cascade="all, delete-orphan")
    activity_events: Mapped[list[ActivityEvent]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def is_premium(self) -> bool:
        return self.subscription_status == "active" and self.subscription_plan == "premium"


class BlacklistedToken(Base):
    """Revoked JWT tokens tracked by their unique JTI claim."""
    __tablename__ = "blacklisted_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    blacklisted_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class LikedBook(Base):
    """A book that a user has liked (swiped right on)."""
    __tablename__ = "liked_books"
    __table_args__ = (
        UniqueConstraint("user_id", "google_book_id", name="uq_user_liked_book"),
        Index("ix_liked_books_liked_at", "liked_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    google_book_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    authors: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    thumbnail: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    liked_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="liked_books")


class SkippedBook(Base):
    """A book that a user has skipped (swiped left on)."""
    __tablename__ = "skipped_books"
    __table_args__ = (
        UniqueConstraint("user_id", "google_book_id", name="uq_user_skipped_book"),
        Index("ix_skipped_books_skipped_at", "skipped_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    google_book_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    skipped_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="skipped_books")


class Category(Base):
    """A book category used to organize and filter book discovery."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    google_category_key: Mapped[str] = mapped_column(String(100), nullable=False)


class DailySwipeCount(Base):
    """Tracks the number of swipes a user has made per day for free tier limits."""
    __tablename__ = "daily_swipe_counts"
    __table_args__ = (
        UniqueConstraint("user_id", "swipe_date", name="uq_user_swipe_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    swipe_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class SwipeEvent(Base):
    """Records each swipe action with book metadata for preference learning."""

    __tablename__ = "swipe_events"
    __table_args__ = (
        Index("ix_swipe_events_user_action", "user_id", "action"),
        Index("ix_swipe_events_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    google_book_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # like, skip, superlike
    genre: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    author: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="swipe_events")


class UserPreference(Base):
    """Aggregated user taste profile computed from swipe history."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    genre_scores: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # JSON
    author_scores: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # JSON
    category_scores: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # JSON
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="preferences")


class DeviceToken(Base):
    """FCM device token for push notification delivery."""

    __tablename__ = "device_tokens"
    __table_args__ = (
        UniqueConstraint("user_id", "token", name="uq_user_device_token"),
        Index("ix_device_tokens_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(500), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), nullable=False, default="android")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="device_tokens")


class NotificationPreference(Base):
    """Per-user notification category preferences."""

    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    recommendations: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    social: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    marketing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    user: Mapped["User"] = relationship(back_populates="notification_preference")


class Notification(Base):
    """Stored notification record for user history/inbox."""

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(String(1000), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
    deep_link: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(back_populates="notifications")


class UserProfile(Base):
    """Extended user profile with bio, avatar, and reading preferences."""

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    bio: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    reading_goal: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="profile")


class Follow(Base):
    """A follow relationship between two users."""

    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follow"),
        Index("ix_follows_follower_id", "follower_id"),
        Index("ix_follows_following_id", "following_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    following_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    follower: Mapped[User] = relationship(foreign_keys=[follower_id])
    following: Mapped[User] = relationship(foreign_keys=[following_id])


class BookList(Base):
    """A curated list of books created by a user."""

    __tablename__ = "book_lists"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False, default="", server_default="")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="book_lists")
    items: Mapped[list[BookListItem]] = relationship(back_populates="book_list", cascade="all, delete-orphan")


class BookListItem(Base):
    """A book entry within a curated book list."""

    __tablename__ = "book_list_items"
    __table_args__ = (
        UniqueConstraint("list_id", "book_id", name="uq_list_book"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("book_lists.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[str] = mapped_column(String(500), nullable=False, default="", server_default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    added_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    book_list: Mapped[BookList] = relationship(back_populates="items")


class BookCover(Base):
    """Processed cover images stored in S3 with multiple size variants."""

    __tablename__ = "book_covers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    book_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    thumbnail_url: Mapped[str] = mapped_column(String(500), nullable=False)
    card_url: Mapped[str] = mapped_column(String(500), nullable=False)
    detail_url: Mapped[str] = mapped_column(String(500), nullable=False)
    blurhash: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    processed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class ActivityEvent(Base):
    """Records user activity for social feed display."""

    __tablename__ = "activity_events"
    __table_args__ = (
        Index("ix_activity_events_user_created", "user_id", "created_at"),
        Index("ix_activity_events_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # liked_book, created_list, followed_user
    event_data: Mapped[str] = mapped_column("metadata", Text, nullable=False, default="{}", server_default="{}")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="activity_events")


SEED_CATEGORIES = [
    {"name": "Fiction", "google_category_key": "fiction"},
    {"name": "Romance", "google_category_key": "romance"},
    {"name": "Mystery", "google_category_key": "mystery"},
    {"name": "Sci-Fi", "google_category_key": "science+fiction"},
    {"name": "Fantasy", "google_category_key": "fantasy"},
    {"name": "Thriller", "google_category_key": "thriller"},
    {"name": "Biography", "google_category_key": "biography"},
    {"name": "History", "google_category_key": "history"},
    {"name": "Self-Help", "google_category_key": "self-help"},
    {"name": "Science", "google_category_key": "science"},
    {"name": "Business", "google_category_key": "business"},
    {"name": "Poetry", "google_category_key": "poetry"},
    {"name": "Horror", "google_category_key": "horror"},
    {"name": "Comics", "google_category_key": "comics"},
]
