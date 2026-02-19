"""Analytics router: detailed analytics endpoints for the admin dashboard."""

import logging

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    CategoryBreakdown,
    DetailedAnalyticsResponse,
    EngagementMetrics,
    PopularBooks,
    RetentionData,
    SwipeStats,
)
from app.services.admin import require_admin
from app.services.analytics import (
    get_category_breakdown,
    get_engagement_metrics,
    get_full_analytics,
    get_popular_books,
    get_retention_data,
    get_swipe_stats,
)
from app.services.auth import get_current_user

logger = logging.getLogger("bookswipe")
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/api/admin/analytics", tags=["analytics"])


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the current user is an admin."""
    return require_admin(current_user)


@router.get("/detailed", response_model=DetailedAnalyticsResponse)
@limiter.limit("10/minute")
def detailed_analytics(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return comprehensive analytics for the admin dashboard."""
    return DetailedAnalyticsResponse(**get_full_analytics(db))


@router.get("/engagement", response_model=EngagementMetrics)
@limiter.limit("10/minute")
def engagement(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return user engagement metrics."""
    return EngagementMetrics(**get_engagement_metrics(db))


@router.get("/swipes", response_model=SwipeStats)
@limiter.limit("10/minute")
def swipes(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return swipe statistics."""
    return SwipeStats(**get_swipe_stats(db))


@router.get("/popular-books", response_model=PopularBooks)
@limiter.limit("10/minute")
def popular_books(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return popular books data."""
    return PopularBooks(**get_popular_books(db))


@router.get("/retention", response_model=RetentionData)
@limiter.limit("10/minute")
def retention(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return retention cohort data."""
    return RetentionData(**get_retention_data(db))


@router.get("/categories", response_model=CategoryBreakdown)
@limiter.limit("10/minute")
def categories(
    request: Request,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return category breakdown."""
    return CategoryBreakdown(**get_category_breakdown(db))
