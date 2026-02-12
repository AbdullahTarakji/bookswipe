"""Google Books API integration with caching and per-user rate limiting."""

import time
from typing import Any

import httpx
from cachetools import TTLCache

from app.config import settings
from app.schemas import BookDetail, BookSummary

_cache: TTLCache = TTLCache(maxsize=1024, ttl=settings.google_books_cache_ttl)
_rate_limits: dict[int, list[float]] = {}


def _check_rate_limit(user_id: int | None) -> None:
    if user_id is None:
        return
    now = time.time()
    window = settings.rate_limit_window
    key = user_id
    timestamps = _rate_limits.get(key, [])
    timestamps = [t for t in timestamps if now - t < window]
    if len(timestamps) >= settings.rate_limit_requests:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later.",
        )
    timestamps.append(now)
    _rate_limits[key] = timestamps


def _parse_book_summary(item: dict[str, Any]) -> BookSummary:
    info = item.get("volumeInfo", {})
    image_links = info.get("imageLinks", {})
    thumbnail = image_links.get("thumbnail", image_links.get("smallThumbnail", ""))
    # Upgrade to HTTPS
    if thumbnail.startswith("http://"):
        thumbnail = "https://" + thumbnail[7:]
    return BookSummary(
        google_book_id=item["id"],
        title=info.get("title", "Unknown"),
        authors=info.get("authors", []),
        thumbnail=thumbnail,
        categories=info.get("categories", []),
        average_rating=info.get("averageRating"),
        ratings_count=info.get("ratingsCount"),
    )


def _parse_book_detail(item: dict[str, Any]) -> BookDetail:
    info = item.get("volumeInfo", {})
    image_links = info.get("imageLinks", {})
    thumbnail = image_links.get("thumbnail", image_links.get("smallThumbnail", ""))
    if thumbnail.startswith("http://"):
        thumbnail = "https://" + thumbnail[7:]
    return BookDetail(
        google_book_id=item["id"],
        title=info.get("title", "Unknown"),
        authors=info.get("authors", []),
        thumbnail=thumbnail,
        categories=info.get("categories", []),
        average_rating=info.get("averageRating"),
        ratings_count=info.get("ratingsCount"),
        description=info.get("description", ""),
        page_count=info.get("pageCount"),
        published_date=info.get("publishedDate"),
        publisher=info.get("publisher"),
        preview_link=info.get("previewLink"),
        info_link=info.get("infoLink"),
    )


async def search_books(
    category: str,
    page: int = 1,
    page_size: int = 20,
    exclude_ids: set[str] | None = None,
    user_id: int | None = None,
) -> tuple[list[BookSummary], int]:
    """Search for books by category via the Google Books API.

    Args:
        category: The subject category to search for.
        page: Page number (1-indexed) for pagination.
        page_size: Number of results per page.
        exclude_ids: Optional set of Google Book IDs to filter out.
        user_id: Optional user ID for per-user rate limiting.

    Returns:
        A tuple of (list of book summaries, total result count).

    Raises:
        HTTPException: 429 if user rate limit exceeded, 502 if API error.
    """
    _check_rate_limit(user_id)

    start_index = (page - 1) * page_size
    cache_key = f"search:{category}:{start_index}:{page_size}"

    cached = _cache.get(cache_key)
    if cached is not None:
        items, total = cached
    else:
        params: dict[str, Any] = {
            "q": f"subject:{category}",
            "startIndex": start_index,
            "maxResults": page_size,
            "printType": "books",
            "orderBy": "relevance",
            "langRestrict": "en",
        }
        if settings.google_books_api_key:
            params["key"] = settings.google_books_api_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(settings.google_books_api_url, params=params)

        if resp.status_code != 200:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google Books API error",
            )

        data = resp.json()
        total = data.get("totalItems", 0)
        raw_items = data.get("items", [])
        items = [_parse_book_summary(item) for item in raw_items]
        _cache[cache_key] = (items, total)

    if exclude_ids:
        items = [b for b in items if b.google_book_id not in exclude_ids]

    return items, total


async def get_book_by_id(book_id: str, user_id: int | None = None) -> BookDetail:
    """Fetch detailed book information by Google Books volume ID.

    Args:
        book_id: The Google Books API volume ID.
        user_id: Optional user ID for per-user rate limiting.

    Returns:
        Detailed book information.

    Raises:
        HTTPException: 404 if not found, 429 if rate limited, 502 if API error.
    """
    _check_rate_limit(user_id)

    cache_key = f"book:{book_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{settings.google_books_api_url}/{book_id}"
    params: dict[str, Any] = {}
    if settings.google_books_api_key:
        params["key"] = settings.google_books_api_key

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)

    if resp.status_code == 404:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    if resp.status_code != 200:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Google Books API error",
        )

    detail = _parse_book_detail(resp.json())
    _cache[cache_key] = detail
    return detail


def clear_cache() -> None:
    """Clear the book search cache and per-user rate limit tracking."""
    _cache.clear()
    _rate_limits.clear()
