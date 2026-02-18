"""Search router: unified search, autocomplete, search history, and trending."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.repositories.search_repository import SearchRepository
from app.schemas import (
    AutocompleteResponse,
    MessageResponse,
    SearchFilters,
    SearchHistoryItem,
    SearchHistoryResponse,
    TrendingSearch,
    TrendingSearchesResponse,
    UnifiedSearchResponse,
)
from app.services.auth import get_current_user
from app.services.search import unified_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=UnifiedSearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    search_type: str = Query("all", pattern="^(all|books|users|lists)$"),
    category: str | None = Query(None, max_length=100),
    author: str | None = Query(None, max_length=200),
    min_rating: float | None = Query(None, ge=0, le=5),
    year_from: int | None = Query(None, ge=1000, le=2100),
    year_to: int | None = Query(None, ge=1000, le=2100),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unified search across books, users, and lists."""
    repo = SearchRepository(db)

    filters = SearchFilters(
        category=category,
        author=author,
        min_rating=min_rating,
        year_from=year_from,
        year_to=year_to,
    )

    # Record search in history
    repo.add_history(current_user.id, q, search_type)

    return await unified_search(
        query=q,
        repo=repo,
        current_user_id=current_user.id,
        filters=filters,
        page=page,
        page_size=page_size,
        search_type=search_type,
    )


@router.get("/autocomplete", response_model=AutocompleteResponse)
def autocomplete(
    q: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return autocomplete suggestions based on user history and trending."""
    repo = SearchRepository(db)
    suggestions = repo.get_autocomplete_suggestions(q, current_user.id, limit)
    return AutocompleteResponse(suggestions=suggestions)


@router.get("/history", response_model=SearchHistoryResponse)
def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's recent search history."""
    repo = SearchRepository(db)
    items, total = repo.get_history(current_user.id, limit)
    return SearchHistoryResponse(
        items=[
            SearchHistoryItem(
                id=item.id,
                query=item.query,
                search_type=item.search_type,
                created_at=item.created_at,
            )
            for item in items
        ],
        total=total,
    )


@router.delete("/history", response_model=MessageResponse)
def clear_search_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear all search history for the current user."""
    repo = SearchRepository(db)
    count = repo.clear_history(current_user.id)
    return MessageResponse(message=f"Cleared {count} search history entries")


@router.delete("/history/{item_id}", response_model=MessageResponse)
def delete_search_history_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a single search history entry."""
    repo = SearchRepository(db)
    deleted = repo.delete_history_item(current_user.id, item_id)
    if not deleted:
        from app.exceptions import NotFoundError
        raise NotFoundError("Search history entry not found")
    return MessageResponse(message="Search history entry deleted")


@router.get("/trending", response_model=TrendingSearchesResponse)
def get_trending_searches(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return trending search terms."""
    repo = SearchRepository(db)
    trending = repo.get_trending_searches(limit)
    return TrendingSearchesResponse(
        searches=[
            TrendingSearch(query=q, count=c) for q, c in trending
        ]
    )
