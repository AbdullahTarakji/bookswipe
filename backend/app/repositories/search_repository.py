"""Repository for search-related database operations."""

from __future__ import annotations

import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import BookList, BookListItem, SearchHistory, User


class SearchRepository:
    """Encapsulates database queries for search features."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Search History ---

    def add_history(self, user_id: int, query: str, search_type: str = "all") -> SearchHistory:
        """Record a search query in user's history."""
        entry = SearchHistory(user_id=user_id, query=query, search_type=search_type)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_history(self, user_id: int, limit: int = 20) -> tuple[list[SearchHistory], int]:
        """Return recent search history for a user."""
        base = self.db.query(SearchHistory).filter(SearchHistory.user_id == user_id)
        total = base.count()
        items = base.order_by(SearchHistory.created_at.desc()).limit(limit).all()
        return items, total

    def clear_history(self, user_id: int) -> int:
        """Delete all search history for a user. Returns count deleted."""
        count = (
            self.db.query(SearchHistory)
            .filter(SearchHistory.user_id == user_id)
            .delete()
        )
        self.db.commit()
        return count

    def delete_history_item(self, user_id: int, item_id: int) -> bool:
        """Delete a single search history entry. Returns True if deleted."""
        count = (
            self.db.query(SearchHistory)
            .filter(SearchHistory.id == item_id, SearchHistory.user_id == user_id)
            .delete()
        )
        self.db.commit()
        return count > 0

    # --- Trending ---

    def get_trending_searches(self, limit: int = 10, days: int = 7) -> list[tuple[str, int]]:
        """Return most popular search queries in the last N days."""
        cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=days)
        results = (
            self.db.query(SearchHistory.query, func.count(SearchHistory.id).label("cnt"))
            .filter(SearchHistory.created_at >= cutoff)
            .group_by(SearchHistory.query)
            .order_by(func.count(SearchHistory.id).desc())
            .limit(limit)
            .all()
        )
        return [(r[0], r[1]) for r in results]

    # --- User Search ---

    def search_users(self, query: str, page: int, page_size: int) -> tuple[list[User], int]:
        """Search users by email prefix match."""
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

    # --- List Search ---

    def search_lists(self, query: str, page: int, page_size: int) -> tuple[list[BookList], int]:
        """Search public book lists by name or description."""
        search_filter = (
            BookList.name.ilike(f"%{query}%") | BookList.description.ilike(f"%{query}%")
        )
        db_query = self.db.query(BookList).filter(search_filter, BookList.is_public.is_(True))
        total = db_query.count()
        lists = (
            db_query.order_by(BookList.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return lists, total

    def get_list_item_count(self, list_id: int) -> int:
        """Return number of items in a book list."""
        return self.db.query(BookListItem).filter(BookListItem.list_id == list_id).count()

    # --- Autocomplete ---

    def get_autocomplete_suggestions(self, prefix: str, user_id: int, limit: int = 5) -> list[str]:
        """Return autocomplete suggestions from user's history and trending."""
        user_results = (
            self.db.query(SearchHistory.query)
            .filter(
                SearchHistory.user_id == user_id,
                SearchHistory.query.ilike(f"{prefix}%"),
            )
            .distinct()
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        suggestions = [r[0] for r in user_results]

        if len(suggestions) < limit:
            remaining = limit - len(suggestions)
            trending = (
                self.db.query(SearchHistory.query)
                .filter(SearchHistory.query.ilike(f"{prefix}%"))
                .group_by(SearchHistory.query)
                .order_by(func.count(SearchHistory.id).desc())
                .limit(remaining)
                .all()
            )
            for r in trending:
                if r[0] not in suggestions:
                    suggestions.append(r[0])
                    if len(suggestions) >= limit:
                        break

        return suggestions[:limit]
