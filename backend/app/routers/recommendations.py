"""Recommendation router: personalised book suggestions, swipe events, and user preferences."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas import (
    PaginatedRecommendations,
    SwipeEventCreate,
    SwipeEventResponse,
    UserPreferenceResponse,
)
from app.services.auth import get_current_user
from app.services.recommendation import get_recommendations, invalidate_recommendation_cache

router = APIRouter(prefix="/api", tags=["recommendations"])


@router.get("/recommendations", response_model=PaginatedRecommendations)
async def recommendations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=40),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return personalised book recommendations for the authenticated user."""
    books, total = await get_recommendations(
        user_id=current_user.id, db=db, page=page, page_size=page_size
    )
    return PaginatedRecommendations(books=books, total=total, page=page, page_size=page_size)


@router.post("/swipe-events", response_model=SwipeEventResponse, status_code=status.HTTP_201_CREATED)
async def create_swipe_event(
    body: SwipeEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a swipe event with book metadata for preference learning."""
    repo = RecommendationRepository(db)
    event = repo.create_swipe_event(
        user_id=current_user.id,
        google_book_id=body.google_book_id,
        action=body.action,
        genre=body.genre,
        author=body.author,
        category=body.category,
    )
    await invalidate_recommendation_cache(current_user.id)
    return event


@router.get("/user/preferences", response_model=UserPreferenceResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's computed taste preferences."""
    repo = RecommendationRepository(db)
    pref = repo.get_user_preference(current_user.id)
    if pref is None:
        return UserPreferenceResponse(
            genre_scores={}, author_scores={}, category_scores={}
        )
    return UserPreferenceResponse(
        genre_scores=json.loads(pref.genre_scores),
        author_scores=json.loads(pref.author_scores),
        category_scores=json.loads(pref.category_scores),
        updated_at=pref.updated_at,
    )
