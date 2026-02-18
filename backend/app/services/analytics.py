"""Analytics service: business logic for the analytics dashboard."""

from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from app.repositories.analytics_repository import AnalyticsRepository


def get_engagement_metrics(db: Session) -> dict:
    """User engagement: DAU, WAU, MAU, signups over time."""
    repo = AnalyticsRepository(db)
    today = datetime.date.today()
    return {
        "dau": repo.get_dau(today),
        "wau": repo.get_wau(today),
        "mau": repo.get_mau(today),
        "signups_over_time": repo.get_signups_over_time(30),
    }


def get_swipe_stats(db: Session) -> dict:
    """Swipe statistics: totals, ratio, average, time series."""
    repo = AnalyticsRepository(db)
    totals = repo.get_swipe_totals()
    total_likes = totals["total_likes"]
    total_skips = totals["total_skips"]
    total = totals["total_swipes"]

    like_ratio = round(total_likes / total * 100, 1) if total > 0 else 0
    skip_ratio = round(total_skips / total * 100, 1) if total > 0 else 0

    return {
        "total_swipes": total,
        "total_likes": total_likes,
        "total_skips": total_skips,
        "like_ratio": like_ratio,
        "skip_ratio": skip_ratio,
        "swipes_per_user_avg": repo.get_swipes_per_user_avg(),
        "swipes_over_time": repo.get_swipes_over_time(30),
    }


def get_popular_books(db: Session) -> dict:
    """Popular books: most liked, most swiped, trending this week."""
    repo = AnalyticsRepository(db)
    return {
        "most_liked": repo.get_most_liked_books(10),
        "most_swiped": repo.get_most_swiped_books(10),
        "trending_this_week": repo.get_trending_books_this_week(10),
    }


def get_retention_data(db: Session) -> dict:
    """Simplified retention cohorts."""
    repo = AnalyticsRepository(db)
    return {
        "cohorts": repo.get_retention_cohorts(4),
    }


def get_category_breakdown(db: Session) -> dict:
    """Category breakdown: likes and activity by category."""
    repo = AnalyticsRepository(db)
    return {
        "likes_by_category": repo.get_likes_by_category(15),
        "most_active_categories": repo.get_most_active_categories(15),
    }


def get_full_analytics(db: Session) -> dict:
    """Aggregate all analytics into a single response."""
    return {
        "engagement": get_engagement_metrics(db),
        "swipes": get_swipe_stats(db),
        "popular_books": get_popular_books(db),
        "retention": get_retention_data(db),
        "categories": get_category_breakdown(db),
    }
