"""Google Books API client with caching, rate limiting, and error handling."""

import logging
import time
from typing import Any

import httpx
from cachetools import TTLCache

from app.config import settings
from app.exceptions import ExternalAPIError, NotFoundError, RateLimitError
from app.schemas import BookDetail, BookSummary

logger = logging.getLogger("bookswipe.google_books")

_cache: TTLCache = TTLCache(maxsize=1024, ttl=settings.google_books_cache_ttl)
_rate_limits: dict[int, list[float]] = {}


def _check_rate_limit(user_id: int | None) -> None:
    """Enforce per-user rate limits for Google Books API calls."""
    if user_id is None:
        return
    now = time.time()
    window = settings.rate_limit_window
    key = user_id
    timestamps = _rate_limits.get(key, [])
    timestamps = [t for t in timestamps if now - t < window]
    if len(timestamps) >= settings.rate_limit_requests:
        raise RateLimitError()
    timestamps.append(now)
    _rate_limits[key] = timestamps


def _parse_book_summary(item: dict[str, Any]) -> BookSummary:
    """Extract a BookSummary from a Google Books API item."""
    info = item.get("volumeInfo", {})
    image_links = info.get("imageLinks", {})
    thumbnail = image_links.get("thumbnail", image_links.get("smallThumbnail", ""))
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
    """Extract a BookDetail from a Google Books API item."""
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
    """Search Google Books by category with caching and rate limiting."""
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

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(settings.google_books_api_url, params=params)
        except httpx.TimeoutException:
            logger.error("Google Books API timeout for category=%s", category)
            raise ExternalAPIError(
                message="Google Books API timed out",
                details={"category": category},
            )
        except httpx.ConnectError:
            logger.error("Google Books API connection error")
            raise ExternalAPIError(
                message="Cannot connect to Google Books API",
            )

        if resp.status_code == 429:
            logger.warning("Google Books API rate limit hit")
            raise ExternalAPIError(
                message="Google Books API rate limit exceeded. Try again later.",
                code="GOOGLE_RATE_LIMIT",
            )
        if resp.status_code != 200:
            logger.error(
                "Google Books API error: status=%d body=%s",
                resp.status_code,
                resp.text[:200],
            )
            raise ExternalAPIError(message="Google Books API error")

        data = resp.json()
        total = data.get("totalItems", 0)
        raw_items = data.get("items", [])
        items = [_parse_book_summary(item) for item in raw_items]
        _cache[cache_key] = (items, total)

    if exclude_ids:
        items = [b for b in items if b.google_book_id not in exclude_ids]

    return items, total


async def get_book_by_id(book_id: str, user_id: int | None = None) -> BookDetail:
    """Fetch a single book by ID from Google Books API."""
    _check_rate_limit(user_id)

    cache_key = f"book:{book_id}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    url = f"{settings.google_books_api_url}/{book_id}"
    params: dict[str, Any] = {}
    if settings.google_books_api_key:
        params["key"] = settings.google_books_api_key

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
    except httpx.TimeoutException:
        logger.error("Google Books API timeout for book_id=%s", book_id)
        raise ExternalAPIError(
            message="Google Books API timed out",
            details={"book_id": book_id},
        )
    except httpx.ConnectError:
        logger.error("Google Books API connection error for book_id=%s", book_id)
        raise ExternalAPIError(message="Cannot connect to Google Books API")

    if resp.status_code == 404:
        raise NotFoundError(message="Book not found")
    if resp.status_code == 429:
        logger.warning("Google Books API rate limit hit for book_id=%s", book_id)
        raise ExternalAPIError(
            message="Google Books API rate limit exceeded. Try again later.",
            code="GOOGLE_RATE_LIMIT",
        )
    if resp.status_code != 200:
        logger.error(
            "Google Books API error: status=%d body=%s",
            resp.status_code,
            resp.text[:200],
        )
        raise ExternalAPIError(message="Google Books API error")

    detail = _parse_book_detail(resp.json())
    _cache[cache_key] = detail
    return detail


def clear_cache() -> None:
    """Clear the book cache and rate limit tracking."""
    _cache.clear()
    _rate_limits.clear()
