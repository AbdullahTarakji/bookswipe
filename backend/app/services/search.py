"""Search service that aggregates results from Google Books API and local database."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.repositories.search_repository import SearchRepository
from app.schemas import (
    AutocompleteResponse,
    BookSearchResult,
    ListSearchResult,
    SearchFilters,
    UnifiedSearchResponse,
    UserSearchResult,
)
from app.services.cache import cache_get, cache_set


def _username_from_email(email: str) -> str:
    """Derive display name from user email."""
    return email.split("@")[0]


async def search_books_google(
    query: str,
    filters: SearchFilters | None = None,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[BookSearchResult], int]:
    """Search Google Books API with optional filters."""
    q_parts = [query]
    if filters:
        if filters.category:
            q_parts.append(f"subject:{filters.category}")
        if filters.author:
            q_parts.append(f"inauthor:{filters.author}")

    q = "+".join(q_parts)
    start_index = (page - 1) * page_size

    cache_key = f"search:books:{q}:{start_index}:{page_size}"
    cached = await cache_get(cache_key)

    if cached is not None:
        books = [BookSearchResult(**b) for b in cached["items"]]
        return books, cached["total"]

    params: dict[str, Any] = {
        "q": q,
        "startIndex": start_index,
        "maxResults": page_size,
        "printType": "books",
        "orderBy": "relevance",
        "langRestrict": "en",
    }
    if settings.google_books_api_key:
        params["key"] = settings.google_books_api_key

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(settings.google_books_api_url, params=params)
    except httpx.RequestError:
        return [], 0

    if resp.status_code != 200:
        return [], 0

    data = resp.json()
    total = data.get("totalItems", 0)
    raw_items = data.get("items", [])

    books = []
    for item in raw_items:
        info = item.get("volumeInfo", {})
        image_links = info.get("imageLinks", {})
        thumbnail = image_links.get("thumbnail", image_links.get("smallThumbnail", ""))
        book_id = item.get("id", "")
        if book_id:
            thumbnail = f"/api/books/cover-proxy/{book_id}?v=2"

        book = BookSearchResult(
            google_book_id=book_id,
            title=info.get("title", "Unknown"),
            authors=info.get("authors", []),
            thumbnail=thumbnail,
            categories=info.get("categories", []),
            average_rating=info.get("averageRating"),
            published_date=info.get("publishedDate"),
        )

        if filters:
            if filters.min_rating and (book.average_rating or 0) < filters.min_rating:
                continue
            if filters.year_from or filters.year_to:
                year = _extract_year(book.published_date)
                if year:
                    if filters.year_from and year < filters.year_from:
                        continue
                    if filters.year_to and year > filters.year_to:
                        continue

        books.append(book)

    await cache_set(
        cache_key,
        {"items": [b.model_dump() for b in books], "total": total},
        ttl=300,
    )

    return books, total


def _extract_year(date_str: str | None) -> int | None:
    """Extract year from a date string like '2023' or '2023-01-15'."""
    if not date_str:
        return None
    try:
        return int(date_str[:4])
    except (ValueError, IndexError):
        return None


async def unified_search(
    query: str,
    repo: SearchRepository,
    current_user_id: int,
    filters: SearchFilters | None = None,
    page: int = 1,
    page_size: int = 10,
    search_type: str = "all",
) -> UnifiedSearchResponse:
    """Perform unified search across books, users, and lists."""
    books: list[BookSearchResult] = []
    users: list[UserSearchResult] = []
    lists: list[ListSearchResult] = []
    total_books = total_users = total_lists = 0

    if search_type in ("all", "books"):
        books, total_books = await search_books_google(query, filters, page, page_size)

    if search_type in ("all", "users"):
        from app.repositories.social_repository import SocialRepository

        social_repo = SocialRepository(repo.db)
        found_users, total_users = repo.search_users(query, page, page_size)
        following_ids = social_repo.get_following_ids(current_user_id)
        users = [
            UserSearchResult(
                user_id=u.id,
                username=_username_from_email(u.email),
                avatar_url=u.profile.avatar_url if u.profile else None,
                bio=u.profile.bio if u.profile else "",
                is_following=u.id in following_ids,
            )
            for u in found_users
            if u.id != current_user_id
        ]
        total_users = len(users) if search_type == "all" else total_users

    if search_type in ("all", "lists"):
        found_lists, total_lists = repo.search_lists(query, page, page_size)
        lists = [
            ListSearchResult(
                id=bl.id,
                name=bl.name,
                description=bl.description,
                user_id=bl.user_id,
                username=_username_from_email(bl.user.email) if bl.user else "",
                item_count=repo.get_list_item_count(bl.id),
                is_public=bl.is_public,
            )
            for bl in found_lists
        ]

    return UnifiedSearchResponse(
        books=books,
        users=users,
        lists=lists,
        total_books=total_books,
        total_users=total_users,
        total_lists=total_lists,
    )
