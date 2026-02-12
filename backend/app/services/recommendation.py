"""Recommendation service with content-based filtering and cold-start handling."""

from __future__ import annotations

import json
import logging
from collections import defaultdict

from sqlalchemy.orm import Session

from app.repositories.recommendation_repository import RecommendationRepository
from app.schemas import BookSummary
from app.services.cache import cache_delete, cache_get, cache_set
from app.services.google_books import search_books

logger = logging.getLogger("bookswipe")

# Scoring weights
WEIGHT_GENRE = 0.4
WEIGHT_AUTHOR = 0.3
WEIGHT_CATEGORY = 0.2
WEIGHT_POPULARITY = 0.1

COLD_START_THRESHOLD = 5
CACHE_TTL = 3600  # 1 hour
TRENDING_CATEGORIES = ["fiction", "thriller", "romance", "science+fiction", "mystery"]


def compute_preference_scores(
    events: list,
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """Compute normalised preference scores from swipe events.

    Likes add +1.0, superlikes +2.0, skips add -0.3 to the respective
    genre/author/category tallies.  Scores are then normalised to [0, 1].

    Returns (genre_scores, author_scores, category_scores).
    """
    genre_counts: dict[str, float] = defaultdict(float)
    author_counts: dict[str, float] = defaultdict(float)
    category_counts: dict[str, float] = defaultdict(float)

    for ev in events:
        if ev.action == "superlike":
            weight = 2.0
        elif ev.action == "like":
            weight = 1.0
        else:
            weight = -0.3

        if ev.genre:
            for g in ev.genre.split(","):
                g = g.strip()
                if g:
                    genre_counts[g] += weight
        if ev.author:
            for a in ev.author.split(","):
                a = a.strip()
                if a:
                    author_counts[a] += weight
        if ev.category:
            for c in ev.category.split(","):
                c = c.strip()
                if c:
                    category_counts[c] += weight

    def _normalise(scores: dict[str, float]) -> dict[str, float]:
        if not scores:
            return {}
        # Clamp negatives to 0
        scores = {k: max(v, 0.0) for k, v in scores.items()}
        max_val = max(scores.values()) if scores else 1.0
        if max_val == 0:
            return {k: 0.0 for k in scores}
        return {k: round(v / max_val, 4) for k, v in scores.items()}

    return _normalise(genre_counts), _normalise(author_counts), _normalise(category_counts)


def score_book(
    book: BookSummary,
    genre_scores: dict[str, float],
    author_scores: dict[str, float],
    category_scores: dict[str, float],
) -> float:
    """Score a candidate book against user preferences.

    Uses weighted formula:
      genre_match * 0.4 + author_match * 0.3 + category_match * 0.2 + popularity * 0.1
    """
    # Genre match: average score of book's categories against genre preferences
    genre_match = 0.0
    if book.categories:
        matches = [genre_scores.get(g, 0.0) for g in book.categories]
        genre_match = sum(matches) / len(matches)

    # Author match
    author_match = 0.0
    if book.authors:
        matches = [author_scores.get(a, 0.0) for a in book.authors]
        author_match = sum(matches) / len(matches)

    # Category match (use book.categories since Google Books uses the same field)
    category_match = 0.0
    if book.categories:
        matches = [category_scores.get(c, 0.0) for c in book.categories]
        category_match = sum(matches) / len(matches)

    # Popularity: normalised rating (0-5 scale -> 0-1)
    popularity = 0.0
    if book.average_rating is not None:
        popularity = min(book.average_rating / 5.0, 1.0)

    return (
        WEIGHT_GENRE * genre_match
        + WEIGHT_AUTHOR * author_match
        + WEIGHT_CATEGORY * category_match
        + WEIGHT_POPULARITY * popularity
    )


async def get_recommendations(
    user_id: int,
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[BookSummary], int]:
    """Return personalised book recommendations for a user.

    Cold-start users (< 5 swipes) receive trending/popular books.
    Established users get content-based filtered results ranked by score.
    Results are cached in Redis for 1 hour.
    """
    cache_key = f"recs:{user_id}:{page}:{page_size}"
    cached = await cache_get(cache_key)
    if cached is not None:
        books = [BookSummary(**b) for b in cached["books"]]
        return books, cached["total"]

    repo = RecommendationRepository(db)
    swipe_count = repo.count_swipe_events(user_id)
    excluded = repo.get_swiped_book_ids(user_id)

    if swipe_count < COLD_START_THRESHOLD:
        books, total = await _cold_start_recommendations(excluded, page, page_size)
    else:
        books, total = await _personalised_recommendations(
            user_id, repo, excluded, page, page_size
        )

    await cache_set(
        cache_key,
        {"books": [b.model_dump() for b in books], "total": total},
        ttl=CACHE_TTL,
    )
    return books, total


async def _cold_start_recommendations(
    excluded: set[str],
    page: int,
    page_size: int,
) -> tuple[list[BookSummary], int]:
    """Return trending/popular books for users with insufficient swipe history."""
    all_books: list[BookSummary] = []
    for cat in TRENDING_CATEGORIES:
        cat_books, _ = await search_books(
            category=cat, page=1, page_size=10, exclude_ids=excluded
        )
        all_books.extend(cat_books)

    # Deduplicate
    seen: set[str] = set()
    unique: list[BookSummary] = []
    for b in all_books:
        if b.google_book_id not in seen and b.google_book_id not in excluded:
            seen.add(b.google_book_id)
            unique.append(b)

    # Sort by popularity
    unique.sort(key=lambda b: (b.average_rating or 0, b.ratings_count or 0), reverse=True)

    total = len(unique)
    start = (page - 1) * page_size
    return unique[start : start + page_size], total


async def _personalised_recommendations(
    user_id: int,
    repo: RecommendationRepository,
    excluded: set[str],
    page: int,
    page_size: int,
) -> tuple[list[BookSummary], int]:
    """Return content-based filtered recommendations for established users."""
    pref = repo.get_user_preference(user_id)
    if pref is None:
        # Preferences not yet computed — compute on-the-fly
        genre_scores, author_scores, category_scores = _compute_from_events(repo, user_id)
    else:
        genre_scores = json.loads(pref.genre_scores)
        author_scores = json.loads(pref.author_scores)
        category_scores = json.loads(pref.category_scores)

    # Determine search categories from top genre preferences
    top_genres = repo.get_top_genres(user_id, limit=5)
    search_cats = top_genres if top_genres else TRENDING_CATEGORIES

    all_books: list[BookSummary] = []
    for cat in search_cats:
        cat_books, _ = await search_books(
            category=cat, page=1, page_size=20, exclude_ids=excluded
        )
        all_books.extend(cat_books)

    # Deduplicate and exclude already-swiped
    seen: set[str] = set()
    unique: list[BookSummary] = []
    for b in all_books:
        if b.google_book_id not in seen and b.google_book_id not in excluded:
            seen.add(b.google_book_id)
            unique.append(b)

    # Score and sort
    scored = [(score_book(b, genre_scores, author_scores, category_scores), b) for b in unique]
    scored.sort(key=lambda x: x[0], reverse=True)

    results = [b for _, b in scored]
    total = len(results)
    start = (page - 1) * page_size
    return results[start : start + page_size], total


def _compute_from_events(
    repo: RecommendationRepository, user_id: int
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    """Compute preference scores directly from swipe events."""
    events = repo.get_swipe_events(user_id)
    return compute_preference_scores(events)


async def invalidate_recommendation_cache(user_id: int) -> None:
    """Clear cached recommendations for a user after a new swipe."""
    # Delete common page keys
    for page in range(1, 6):
        for ps in (10, 20):
            await cache_delete(f"recs:{user_id}:{page}:{ps}")


def compute_and_store_preferences(db: Session, user_id: int) -> None:
    """Batch-compute and persist user preferences from swipe history.

    Called by the background worker.
    """
    repo = RecommendationRepository(db)
    events = repo.get_swipe_events(user_id)
    if not events:
        return
    genre_scores, author_scores, category_scores = compute_preference_scores(events)
    repo.upsert_user_preference(user_id, genre_scores, author_scores, category_scores)
