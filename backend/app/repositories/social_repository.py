"""Repository for social feature database operations (follows, activity)."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models import ActivityEvent, Follow, LikedBook, User, UserProfile


class SocialRepository:
    """Encapsulates database queries for follows and activity events."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Profile ---

    def get_profile(self, user_id: int) -> UserProfile | None:
        """Return the profile for a user, or None."""
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    def create_profile(self, user_id: int) -> UserProfile:
        """Create a default profile for a user."""
        profile = UserProfile(user_id=user_id)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def update_profile(self, profile: UserProfile, **kwargs: object) -> UserProfile:
        """Update profile fields and persist."""
        for key, value in kwargs.items():
            if value is not None:
                setattr(profile, key, value)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_or_create_profile(self, user_id: int) -> UserProfile:
        """Return existing profile or create a new default one."""
        profile = self.get_profile(user_id)
        if profile is None:
            profile = self.create_profile(user_id)
        return profile

    # --- Follows ---

    def get_follow(self, follower_id: int, following_id: int) -> Follow | None:
        """Return a follow relationship, or None."""
        return (
            self.db.query(Follow)
            .filter(Follow.follower_id == follower_id, Follow.following_id == following_id)
            .first()
        )

    def create_follow(self, follower_id: int, following_id: int) -> Follow:
        """Create a new follow relationship."""
        follow = Follow(follower_id=follower_id, following_id=following_id)
        self.db.add(follow)
        self.db.commit()
        self.db.refresh(follow)
        return follow

    def delete_follow(self, follow: Follow) -> None:
        """Remove a follow relationship."""
        self.db.delete(follow)
        self.db.commit()

    def get_followers(self, user_id: int, page: int, page_size: int) -> tuple[list[User], int]:
        """Return paginated list of users who follow the given user."""
        query = (
            self.db.query(User)
            .join(Follow, Follow.follower_id == User.id)
            .filter(Follow.following_id == user_id, User.is_active.is_(True))
        )
        total = query.count()
        users = (
            query.order_by(Follow.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return users, total

    def get_following(self, user_id: int, page: int, page_size: int) -> tuple[list[User], int]:
        """Return paginated list of users the given user follows."""
        query = (
            self.db.query(User)
            .join(Follow, Follow.following_id == User.id)
            .filter(Follow.follower_id == user_id, User.is_active.is_(True))
        )
        total = query.count()
        users = (
            query.order_by(Follow.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return users, total

    def get_followers_count(self, user_id: int) -> int:
        """Return number of followers for a user."""
        return self.db.query(Follow).filter(Follow.following_id == user_id).count()

    def get_following_count(self, user_id: int) -> int:
        """Return number of users a user follows."""
        return self.db.query(Follow).filter(Follow.follower_id == user_id).count()

    def is_following(self, follower_id: int, following_id: int) -> bool:
        """Check if follower_id follows following_id."""
        return self.get_follow(follower_id, following_id) is not None

    def get_following_ids(self, user_id: int) -> set[int]:
        """Return set of user IDs that the given user follows."""
        rows = self.db.query(Follow.following_id).filter(Follow.follower_id == user_id).all()
        return {row[0] for row in rows}

    # --- Activity ---

    def create_activity(self, user_id: int, event_type: str, event_metadata: dict | None = None) -> ActivityEvent:
        """Create a new activity event."""
        event = ActivityEvent(
            user_id=user_id,
            event_type=event_type,
            event_data=json.dumps(event_metadata or {}),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_feed(self, user_ids: list[int], page: int, page_size: int) -> tuple[list[ActivityEvent], int]:
        """Return paginated activity events for a set of users."""
        query = self.db.query(ActivityEvent).filter(ActivityEvent.user_id.in_(user_ids))
        total = query.count()
        events = (
            query.order_by(ActivityEvent.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return events, total

    def get_user_activity(self, user_id: int, page: int, page_size: int) -> tuple[list[ActivityEvent], int]:
        """Return paginated activity events for a single user."""
        query = self.db.query(ActivityEvent).filter(ActivityEvent.user_id == user_id)
        total = query.count()
        events = (
            query.order_by(ActivityEvent.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return events, total

    # --- Stats ---

    def get_liked_books_count(self, user_id: int) -> int:
        """Return number of books liked by user."""
        return self.db.query(LikedBook).filter(LikedBook.user_id == user_id).count()

    # --- User Search ---

    def search_users(self, query: str, page: int, page_size: int) -> tuple[list[User], int]:
        """Search users by email (prefix match)."""
        search_filter = User.email.ilike(f"%{query}%")
        db_query = self.db.query(User).filter(search_filter, User.is_active.is_(True))
        total = db_query.count()
        users = (
            db_query.order_by(User.email)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return users, total
