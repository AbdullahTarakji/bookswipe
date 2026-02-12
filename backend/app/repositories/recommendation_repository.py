"""Repository for recommendation-related database operations."""

from __future__ import annotations

import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import LikedBook, SkippedBook, SwipeEvent, UserPreference


class RecommendationRepository:
    """Encapsulates database queries for swipe events and user preferences."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Swipe Events ─────────────────────────────────────────

    def create_swipe_event(
        self,
        user_id: int,
        google_book_id: str,
        action: str,
        genre: str = "",
        author: str = "",
        category: str = "",
    ) -> SwipeEvent:
        """Record a new swipe event with book metadata."""
        event = SwipeEvent(
            user_id=user_id,
            google_book_id=google_book_id,
            action=action,
            genre=genre,
            author=author,
            category=category,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_swipe_events(self, user_id: int, limit: int = 500) -> list[SwipeEvent]:
        """Return recent swipe events for a user, newest first."""
        return (
            self.db.query(SwipeEvent)
            .filter(SwipeEvent.user_id == user_id)
            .order_by(SwipeEvent.created_at.desc())
            .limit(limit)
            .all()
        )

    def count_swipe_events(self, user_id: int) -> int:
        """Return the total number of swipe events for a user."""
        return self.db.query(func.count(SwipeEvent.id)).filter(SwipeEvent.user_id == user_id).scalar() or 0

    def get_liked_events(self, user_id: int) -> list[SwipeEvent]:
        """Return all 'like' and 'superlike' swipe events for a user."""
        return (
            self.db.query(SwipeEvent)
            .filter(SwipeEvent.user_id == user_id, SwipeEvent.action.in_(["like", "superlike"]))
            .order_by(SwipeEvent.created_at.desc())
            .all()
        )

    # ── User Preferences ────────────────────────────────────

    def get_user_preference(self, user_id: int) -> UserPreference | None:
        """Return the stored preference profile for a user, or None."""
        return self.db.query(UserPreference).filter(UserPreference.user_id == user_id).first()

    def upsert_user_preference(
        self,
        user_id: int,
        genre_scores: dict[str, float],
        author_scores: dict[str, float],
        category_scores: dict[str, float],
    ) -> UserPreference:
        """Create or update a user's preference profile."""
        pref = self.get_user_preference(user_id)
        if pref is None:
            pref = UserPreference(
                user_id=user_id,
                genre_scores=json.dumps(genre_scores),
                author_scores=json.dumps(author_scores),
                category_scores=json.dumps(category_scores),
            )
            self.db.add(pref)
        else:
            pref.genre_scores = json.dumps(genre_scores)
            pref.author_scores = json.dumps(author_scores)
            pref.category_scores = json.dumps(category_scores)
        self.db.commit()
        self.db.refresh(pref)
        return pref

    # ── Recommendation Candidates ────────────────────────────

    def get_swiped_book_ids(self, user_id: int) -> set[str]:
        """Return the set of Google Book IDs the user has already swiped on."""
        liked_ids = self.db.query(LikedBook.google_book_id).filter(LikedBook.user_id == user_id).all()
        skipped_ids = self.db.query(SkippedBook.google_book_id).filter(SkippedBook.user_id == user_id).all()
        event_ids = self.db.query(SwipeEvent.google_book_id).filter(SwipeEvent.user_id == user_id).all()
        return {row[0] for row in liked_ids} | {row[0] for row in skipped_ids} | {row[0] for row in event_ids}

    def get_top_genres(self, user_id: int, limit: int = 5) -> list[str]:
        """Return the user's top genres based on liked swipe events."""
        rows = (
            self.db.query(SwipeEvent.genre, func.count(SwipeEvent.id).label("cnt"))
            .filter(
                SwipeEvent.user_id == user_id,
                SwipeEvent.action.in_(["like", "superlike"]),
                SwipeEvent.genre != "",
            )
            .group_by(SwipeEvent.genre)
            .order_by(func.count(SwipeEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [row[0] for row in rows]
