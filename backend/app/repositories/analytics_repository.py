"""Repository for analytics-specific database queries."""

from __future__ import annotations

import datetime

from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.models import (
    LikedBook,
    SwipeEvent,
    User,
)


class AnalyticsRepository:
    """Encapsulates all database queries for the analytics dashboard."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ── User Engagement ──────────────────────────────────────────────

    def get_dau(self, date: datetime.date) -> int:
        """Daily active users: users who swiped on a given date."""
        return (
            self.db.query(func.count(distinct(SwipeEvent.user_id)))
            .filter(func.date(SwipeEvent.created_at) == date)
            .scalar()
            or 0
        )

    def get_wau(self, end_date: datetime.date) -> int:
        """Weekly active users: distinct users who swiped in last 7 days."""
        start = end_date - datetime.timedelta(days=6)
        return (
            self.db.query(func.count(distinct(SwipeEvent.user_id)))
            .filter(func.date(SwipeEvent.created_at) >= start)
            .filter(func.date(SwipeEvent.created_at) <= end_date)
            .scalar()
            or 0
        )

    def get_mau(self, end_date: datetime.date) -> int:
        """Monthly active users: distinct users who swiped in last 30 days."""
        start = end_date - datetime.timedelta(days=29)
        return (
            self.db.query(func.count(distinct(SwipeEvent.user_id)))
            .filter(func.date(SwipeEvent.created_at) >= start)
            .filter(func.date(SwipeEvent.created_at) <= end_date)
            .scalar()
            or 0
        )

    def get_signups_over_time(self, days: int = 30) -> list[dict]:
        """Daily new signups for the last N days."""
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
        return [{"date": str(r.date), "count": r.count} for r in rows]

    # ── Swipe Stats ──────────────────────────────────────────────────

    def get_swipe_totals(self) -> dict:
        """Total likes, skips, and overall swipes from SwipeEvent."""
        row = self.db.query(
            func.count(SwipeEvent.id).label("total"),
            func.count(SwipeEvent.id).filter(SwipeEvent.action == "like").label("likes"),
            func.count(SwipeEvent.id).filter(SwipeEvent.action == "skip").label("skips"),
        ).one()
        return {
            "total_swipes": row.total,
            "total_likes": row.likes,
            "total_skips": row.skips,
        }

    def get_swipes_per_user_avg(self) -> float:
        """Average swipes per user (users who have at least 1 swipe)."""
        sub = (
            self.db.query(
                SwipeEvent.user_id,
                func.count(SwipeEvent.id).label("cnt"),
            )
            .group_by(SwipeEvent.user_id)
            .subquery()
        )
        avg = self.db.query(func.avg(sub.c.cnt)).scalar()
        return round(float(avg or 0), 2)

    def get_swipes_over_time(self, days: int = 30) -> list[dict]:
        """Daily swipe counts for the last N days."""
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
        rows = (
            self.db.query(
                func.date(SwipeEvent.created_at).label("date"),
                func.count(SwipeEvent.id).label("count"),
            )
            .filter(SwipeEvent.created_at >= cutoff)
            .group_by(func.date(SwipeEvent.created_at))
            .order_by(func.date(SwipeEvent.created_at))
            .all()
        )
        return [{"date": str(r.date), "count": r.count} for r in rows]

    # ── Popular Books ────────────────────────────────────────────────

    def get_most_liked_books(self, limit: int = 10) -> list[dict]:
        """Books with the most likes."""
        rows = (
            self.db.query(
                LikedBook.google_book_id,
                LikedBook.title,
                LikedBook.authors,
                LikedBook.thumbnail,
                func.count(LikedBook.id).label("like_count"),
            )
            .group_by(LikedBook.google_book_id, LikedBook.title, LikedBook.authors, LikedBook.thumbnail)
            .order_by(func.count(LikedBook.id).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "google_book_id": r.google_book_id,
                "title": r.title,
                "authors": r.authors,
                "thumbnail": r.thumbnail,
                "like_count": r.like_count,
            }
            for r in rows
        ]

    def get_most_swiped_books(self, limit: int = 10) -> list[dict]:
        """Books with the most total swipe events."""
        rows = (
            self.db.query(
                SwipeEvent.google_book_id,
                func.count(SwipeEvent.id).label("swipe_count"),
            )
            .group_by(SwipeEvent.google_book_id)
            .order_by(func.count(SwipeEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [
            {"google_book_id": r.google_book_id, "swipe_count": r.swipe_count}
            for r in rows
        ]

    def get_trending_books_this_week(self, limit: int = 10) -> list[dict]:
        """Books with the most likes in the last 7 days."""
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        rows = (
            self.db.query(
                LikedBook.google_book_id,
                LikedBook.title,
                LikedBook.authors,
                LikedBook.thumbnail,
                func.count(LikedBook.id).label("like_count"),
            )
            .filter(LikedBook.liked_at >= cutoff)
            .group_by(LikedBook.google_book_id, LikedBook.title, LikedBook.authors, LikedBook.thumbnail)
            .order_by(func.count(LikedBook.id).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "google_book_id": r.google_book_id,
                "title": r.title,
                "authors": r.authors,
                "thumbnail": r.thumbnail,
                "like_count": r.like_count,
            }
            for r in rows
        ]

    # ── Retention (simplified) ───────────────────────────────────────

    def get_retention_cohorts(self, weeks: int = 4) -> list[dict]:
        """Simplified weekly retention: for each signup-week cohort,
        what % of users were active (swiped) in subsequent weeks."""
        now = datetime.datetime.now(datetime.timezone.utc)
        cohorts = []

        for w in range(weeks):
            cohort_start = now - datetime.timedelta(weeks=weeks - w)
            cohort_end = cohort_start + datetime.timedelta(days=7)

            # Users who signed up in this week
            cohort_users = (
                self.db.query(User.id)
                .filter(User.created_at >= cohort_start)
                .filter(User.created_at < cohort_end)
                .all()
            )
            cohort_ids = [u.id for u in cohort_users]
            cohort_size = len(cohort_ids)

            if cohort_size == 0:
                cohorts.append({
                    "cohort_week": str(cohort_start.date()),
                    "cohort_size": 0,
                    "retained_week_1": 0,
                    "retained_week_2": 0,
                })
                continue

            # Retained in week after signup
            week1_start = cohort_end
            week1_end = week1_start + datetime.timedelta(days=7)
            retained_1 = (
                self.db.query(func.count(distinct(SwipeEvent.user_id)))
                .filter(SwipeEvent.user_id.in_(cohort_ids))
                .filter(SwipeEvent.created_at >= week1_start)
                .filter(SwipeEvent.created_at < week1_end)
                .scalar()
                or 0
            )

            # Retained in second week
            week2_start = week1_end
            week2_end = week2_start + datetime.timedelta(days=7)
            retained_2 = (
                self.db.query(func.count(distinct(SwipeEvent.user_id)))
                .filter(SwipeEvent.user_id.in_(cohort_ids))
                .filter(SwipeEvent.created_at >= week2_start)
                .filter(SwipeEvent.created_at < week2_end)
                .scalar()
                or 0
            )

            cohorts.append({
                "cohort_week": str(cohort_start.date()),
                "cohort_size": cohort_size,
                "retained_week_1": round(retained_1 / cohort_size * 100, 1),
                "retained_week_2": round(retained_2 / cohort_size * 100, 1),
            })

        return cohorts

    # ── Category Breakdown ───────────────────────────────────────────

    def get_likes_by_category(self, limit: int = 15) -> list[dict]:
        """Likes grouped by SwipeEvent.category (populated at swipe time)."""
        rows = (
            self.db.query(
                SwipeEvent.category,
                func.count(SwipeEvent.id).label("count"),
            )
            .filter(SwipeEvent.action == "like")
            .filter(SwipeEvent.category != "")
            .group_by(SwipeEvent.category)
            .order_by(func.count(SwipeEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [{"category": r.category, "count": r.count} for r in rows]

    def get_most_active_categories(self, limit: int = 15) -> list[dict]:
        """Categories with the most total swipes."""
        rows = (
            self.db.query(
                SwipeEvent.category,
                func.count(SwipeEvent.id).label("count"),
            )
            .filter(SwipeEvent.category != "")
            .group_by(SwipeEvent.category)
            .order_by(func.count(SwipeEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [{"category": r.category, "count": r.count} for r in rows]
