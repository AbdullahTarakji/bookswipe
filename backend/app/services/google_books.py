"""Google Books API integration with Redis caching and per-user rate limiting."""

import time
from typing import Any

import httpx

from app.config import settings
from app.exceptions import ExternalAPIError, NotFoundError, RateLimitError
from app.schemas import BookDetail, BookSummary
from app.services.cache import cache_get, cache_set

_rate_limits: dict[int, list[float]] = {}
_last_eviction: float = 0.0
_EVICTION_INTERVAL: float = 300.0  # purge stale entries every 5 minutes


def _check_rate_limit(user_id: int | None) -> None:
    """Enforce per-user rate limits on Google Books API access."""
    if user_id is None:
        return
    now = time.time()
    window = settings.rate_limit_window

    # Periodically evict stale user entries to prevent unbounded growth
    global _last_eviction
    if now - _last_eviction > _EVICTION_INTERVAL:
        stale_keys = [k for k, v in _rate_limits.items() if not v or now - v[-1] >= window]
        for k in stale_keys:
            del _rate_limits[k]
        _last_eviction = now

    key = user_id
    timestamps = _rate_limits.get(key, [])
    timestamps = [t for t in timestamps if now - t < window]
    if len(timestamps) >= settings.rate_limit_requests:
        raise RateLimitError()
    timestamps.append(now)
    _rate_limits[key] = timestamps


def _parse_book_summary(item: dict[str, Any]) -> BookSummary:
    """Parse a Google Books API volume item into a BookSummary schema."""
    info = item.get("volumeInfo", {})
    image_links = info.get("imageLinks", {})
    thumbnail = image_links.get("thumbnail", image_links.get("smallThumbnail", ""))
    # Upgrade to HTTPS
    if thumbnail.startswith("http://"):
        thumbnail = "https://" + thumbnail[7:]
    # Use cover-proxy with book ID for high-res image lookup
    book_id = item.get("id", "")
    if book_id:
        thumbnail = f"/api/books/cover-proxy/{book_id}?v=2"
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
    """Parse a Google Books API volume item into a BookDetail schema."""
    info = item.get("volumeInfo", {})
    image_links = info.get("imageLinks", {})
    thumbnail = image_links.get("thumbnail", image_links.get("smallThumbnail", ""))
    if thumbnail.startswith("http://"):
        thumbnail = "https://" + thumbnail[7:]
    book_id = item.get("id", "")
    if book_id:
        thumbnail = f"/api/books/cover-proxy/{book_id}?v=2"
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


def _book_summary_to_dict(book: BookSummary) -> dict[str, Any]:
    """Serialize a BookSummary to a JSON-safe dict for caching."""
    return {
        "google_book_id": book.google_book_id,
        "title": book.title,
        "authors": book.authors,
        "thumbnail": book.thumbnail,
        "categories": book.categories,
        "average_rating": book.average_rating,
        "ratings_count": book.ratings_count,
    }


def _dict_to_book_summary(d: dict[str, Any]) -> BookSummary:
    """Deserialize a dict back into a BookSummary."""
    return BookSummary(**d)


def _book_detail_to_dict(book: BookDetail) -> dict[str, Any]:
    """Serialize a BookDetail to a JSON-safe dict for caching."""
    return {
        "google_book_id": book.google_book_id,
        "title": book.title,
        "authors": book.authors,
        "thumbnail": book.thumbnail,
        "categories": book.categories,
        "average_rating": book.average_rating,
        "ratings_count": book.ratings_count,
        "description": book.description,
        "page_count": book.page_count,
        "published_date": book.published_date,
        "publisher": book.publisher,
        "preview_link": book.preview_link,
        "info_link": book.info_link,
    }


def _dict_to_book_detail(d: dict[str, Any]) -> BookDetail:
    """Deserialize a dict back into a BookDetail."""
    return BookDetail(**d)


async def search_books(
    category: str,
    page: int = 1,
    page_size: int = 20,
    exclude_ids: set[str] | None = None,
    user_id: int | None = None,
) -> tuple[list[BookSummary], int]:
    """Search Google Books by category with caching and rate limiting.

    Returns a tuple of (book summaries, total count).
    Raises ExternalAPIError if the Google Books API is unreachable.
    """
    _check_rate_limit(user_id)

    start_index = (page - 1) * page_size
    cache_key = f"search:{category}:{start_index}:{page_size}"

    cached = await cache_get(cache_key)
    if cached is not None:
        items = [_dict_to_book_summary(b) for b in cached["items"]]
        total = cached["total"]
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

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(settings.google_books_api_url, params=params)
        except httpx.RequestError as exc:
            raise ExternalAPIError(
                "Google Books API is unreachable",
                details=str(exc),
            )

        if resp.status_code != 200:
            raise ExternalAPIError("Google Books API error")

        data = resp.json()
        total = data.get("totalItems", 0)
        raw_items = data.get("items", [])
        items = [_parse_book_summary(item) for item in raw_items]
        await cache_set(
            cache_key,
            {"items": [_book_summary_to_dict(b) for b in items], "total": total},
            ttl=settings.google_books_cache_ttl,
        )

    if exclude_ids:
        items = [b for b in items if b.google_book_id not in exclude_ids]

    return items, total


async def get_book_by_id(book_id: str, user_id: int | None = None) -> BookDetail:
    """Fetch a single book's details from Google Books by ID.

    Raises NotFoundError if the book does not exist.
    Raises ExternalAPIError on API failures.
    """
    _check_rate_limit(user_id)

    cache_key = f"book:{book_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return _dict_to_book_detail(cached)

    url = f"{settings.google_books_api_url}/{book_id}"
    params: dict[str, Any] = {}
    if settings.google_books_api_key:
        params["key"] = settings.google_books_api_key

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
    except httpx.RequestError as exc:
        raise ExternalAPIError(
            "Google Books API is unreachable",
            details=str(exc),
        )

    if resp.status_code == 404:
        raise NotFoundError("Book not found")
    if resp.status_code != 200:
        raise ExternalAPIError("Google Books API error")

    detail = _parse_book_detail(resp.json())
    await cache_set(cache_key, _book_detail_to_dict(detail), ttl=settings.book_detail_cache_ttl)
    return detail


def clear_cache() -> None:
    """Clear rate limit counters (for testing). Redis cache is mocked in tests."""
    _rate_limits.clear()
