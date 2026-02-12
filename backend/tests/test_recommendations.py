"""Tests for the recommendation engine: scoring, cold start, cache, and API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import SwipeEvent, UserPreference
from app.schemas import BookSummary
from app.services.recommendation import (
    COLD_START_THRESHOLD,
    WEIGHT_AUTHOR,
    WEIGHT_CATEGORY,
    WEIGHT_GENRE,
    WEIGHT_POPULARITY,
    compute_preference_scores,
    score_book,
)

from tests.conftest import VALID_TEST_PASSWORD, TestingSessionLocal


# ── Unit tests: scoring algorithm ─────────────────────────────


class TestComputePreferenceScores:
    """Tests for the preference score computation from swipe events."""

    def _make_event(self, action="like", genre="", author="", category=""):
        ev = MagicMock()
        ev.action = action
        ev.genre = genre
        ev.author = author
        ev.category = category
        return ev

    def test_empty_events(self):
        """Empty event list produces empty scores."""
        genre, author, cat = compute_preference_scores([])
        assert genre == {}
        assert author == {}
        assert cat == {}

    def test_single_like(self):
        """A single like event produces a score of 1.0 for that genre."""
        events = [self._make_event(action="like", genre="Fiction", author="Author A")]
        genre, author, cat = compute_preference_scores(events)
        assert genre == {"Fiction": 1.0}
        assert author == {"Author A": 1.0}

    def test_superlike_weighted_higher(self):
        """Superlikes contribute 2x compared to likes."""
        events = [
            self._make_event(action="like", genre="Fiction"),
            self._make_event(action="superlike", genre="Romance"),
        ]
        genre, _, _ = compute_preference_scores(events)
        assert genre["Romance"] == 1.0  # highest (2.0 normalised)
        assert genre["Fiction"] == 0.5  # 1.0 / 2.0

    def test_skip_reduces_score(self):
        """Skips reduce scores; negative values are clamped to 0."""
        events = [
            self._make_event(action="skip", genre="Horror"),
        ]
        genre, _, _ = compute_preference_scores(events)
        assert genre["Horror"] == 0.0  # clamped

    def test_mixed_genres(self):
        """Multiple genres are each tracked independently."""
        events = [
            self._make_event(action="like", genre="Fiction"),
            self._make_event(action="like", genre="Fiction"),
            self._make_event(action="like", genre="Romance"),
        ]
        genre, _, _ = compute_preference_scores(events)
        assert genre["Fiction"] == 1.0
        assert genre["Romance"] == 0.5

    def test_comma_separated_genres(self):
        """Comma-separated genre strings are split into individual genres."""
        events = [self._make_event(action="like", genre="Fiction, Romance")]
        genre, _, _ = compute_preference_scores(events)
        assert "Fiction" in genre
        assert "Romance" in genre

    def test_category_scores(self):
        """Category scores are computed separately from genres."""
        events = [self._make_event(action="like", category="Technology")]
        _, _, cat = compute_preference_scores(events)
        assert cat == {"Technology": 1.0}


class TestScoreBook:
    """Tests for the book scoring function."""

    def _make_book(self, categories=None, authors=None, avg_rating=None, ratings_count=None):
        return BookSummary(
            google_book_id="test_id",
            title="Test",
            authors=authors or [],
            thumbnail="",
            categories=categories or [],
            average_rating=avg_rating,
            ratings_count=ratings_count,
        )

    def test_perfect_match(self):
        """A book matching all preferences scores maximum."""
        genre_scores = {"Fiction": 1.0}
        author_scores = {"Author A": 1.0}
        category_scores = {"Fiction": 1.0}
        book = self._make_book(
            categories=["Fiction"], authors=["Author A"], avg_rating=5.0
        )
        result = score_book(book, genre_scores, author_scores, category_scores)
        expected = WEIGHT_GENRE * 1.0 + WEIGHT_AUTHOR * 1.0 + WEIGHT_CATEGORY * 1.0 + WEIGHT_POPULARITY * 1.0
        assert abs(result - expected) < 0.001

    def test_no_match(self):
        """A book matching no preferences scores only popularity."""
        book = self._make_book(
            categories=["Horror"], authors=["Unknown"], avg_rating=3.0
        )
        result = score_book(book, {"Fiction": 1.0}, {"Author A": 1.0}, {"Fiction": 1.0})
        expected = WEIGHT_POPULARITY * (3.0 / 5.0)
        assert abs(result - expected) < 0.001

    def test_no_rating(self):
        """A book with no rating has 0 popularity score."""
        book = self._make_book(categories=["Fiction"], authors=[])
        result = score_book(book, {"Fiction": 1.0}, {}, {})
        expected = WEIGHT_GENRE * 1.0
        assert abs(result - expected) < 0.001

    def test_partial_author_match(self):
        """Multiple authors are averaged for the author match score."""
        book = self._make_book(authors=["Author A", "Author B"])
        result = score_book(book, {}, {"Author A": 1.0}, {})
        expected = WEIGHT_AUTHOR * 0.5  # average of 1.0 and 0.0
        assert abs(result - expected) < 0.001

    def test_empty_book(self):
        """A book with no metadata scores 0."""
        book = self._make_book()
        result = score_book(book, {"Fiction": 1.0}, {"Author A": 1.0}, {"Fiction": 1.0})
        assert result == 0.0


# ── Integration tests: API endpoints ────────────────────────


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def auth_headers(client):
    resp = client.post("/api/auth/register", json={
        "email": "rec_test@example.com",
        "password": VALID_TEST_PASSWORD,
    })
    data = resp.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


@pytest.fixture()
def auth_user_id(auth_headers, client):
    resp = client.get("/api/auth/me", headers=auth_headers)
    return resp.json()["id"]


class TestSwipeEventsAPI:
    """Tests for POST /api/swipe-events."""

    def test_create_swipe_event(self, client, auth_headers):
        """Recording a swipe event returns 201 with event details."""
        resp = client.post("/api/swipe-events", json={
            "google_book_id": "abc123",
            "action": "like",
            "genre": "Fiction",
            "author": "Test Author",
            "category": "Fiction",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["google_book_id"] == "abc123"
        assert data["action"] == "like"
        assert data["genre"] == "Fiction"

    def test_create_swipe_event_skip(self, client, auth_headers):
        """Skip action is valid."""
        resp = client.post("/api/swipe-events", json={
            "google_book_id": "def456",
            "action": "skip",
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["action"] == "skip"

    def test_create_swipe_event_superlike(self, client, auth_headers):
        """Superlike action is valid."""
        resp = client.post("/api/swipe-events", json={
            "google_book_id": "ghi789",
            "action": "superlike",
            "genre": "Romance",
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["action"] == "superlike"

    def test_invalid_action(self, client, auth_headers):
        """Invalid action is rejected with 422."""
        resp = client.post("/api/swipe-events", json={
            "google_book_id": "abc123",
            "action": "invalid",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_requires_auth(self, client):
        """Unauthenticated requests are rejected."""
        resp = client.post("/api/swipe-events", json={
            "google_book_id": "abc123",
            "action": "like",
        })
        assert resp.status_code == 401


class TestUserPreferencesAPI:
    """Tests for GET /api/user/preferences."""

    def test_empty_preferences(self, client, auth_headers):
        """New user with no swipes returns empty preferences."""
        resp = client.get("/api/user/preferences", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["genre_scores"] == {}
        assert data["author_scores"] == {}
        assert data["category_scores"] == {}

    def test_preferences_after_swipes(self, client, auth_headers, auth_user_id):
        """Preferences reflect stored data after background computation."""
        # Record some swipe events
        for book_id in ["b1", "b2", "b3"]:
            client.post("/api/swipe-events", json={
                "google_book_id": book_id,
                "action": "like",
                "genre": "Fiction",
                "author": "Test Author",
            }, headers=auth_headers)

        # Simulate background worker computing preferences
        from app.services.recommendation import compute_and_store_preferences
        db = TestingSessionLocal()
        try:
            compute_and_store_preferences(db, auth_user_id)
        finally:
            db.close()

        resp = client.get("/api/user/preferences", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "Fiction" in data["genre_scores"]
        assert data["genre_scores"]["Fiction"] == 1.0

    def test_requires_auth(self, client):
        """Unauthenticated requests are rejected."""
        resp = client.get("/api/user/preferences")
        assert resp.status_code == 401


class TestRecommendationsAPI:
    """Tests for GET /api/recommendations."""

    def test_cold_start(self, client, auth_headers):
        """Users with <5 swipes get cold-start (trending) recommendations."""
        mock_books = [
            {
                "google_book_id": f"trending_{i}",
                "title": f"Trending Book {i}",
                "authors": ["Author"],
                "thumbnail": "",
                "categories": ["Fiction"],
                "average_rating": 4.0,
                "ratings_count": 100,
                "description": "",
                "page_count": None,
                "published_date": None,
                "publisher": None,
            }
            for i in range(5)
        ]

        async def mock_search(category, page=1, page_size=20, exclude_ids=None, user_id=None):
            books = [BookSummary(**b) for b in mock_books]
            return books, len(books)

        with patch("app.services.recommendation.search_books", side_effect=mock_search):
            resp = client.get("/api/recommendations", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        assert len(data["books"]) > 0

    def test_personalised_after_swipes(self, client, auth_headers, auth_user_id):
        """Users with >=5 swipes get personalised recommendations."""
        # Create enough swipe events to pass cold start
        db = TestingSessionLocal()
        try:
            for i in range(COLD_START_THRESHOLD + 1):
                db.add(SwipeEvent(
                    user_id=auth_user_id,
                    google_book_id=f"book_{i}",
                    action="like",
                    genre="Fiction",
                    author="Fav Author",
                    category="Fiction",
                ))
            db.commit()
        finally:
            db.close()

        mock_books = [
            {
                "google_book_id": f"rec_{i}",
                "title": f"Rec Book {i}",
                "authors": ["Fav Author"],
                "thumbnail": "",
                "categories": ["Fiction"],
                "average_rating": 4.5,
                "ratings_count": 200,
                "description": "",
                "page_count": None,
                "published_date": None,
                "publisher": None,
            }
            for i in range(5)
        ]

        async def mock_search(category, page=1, page_size=20, exclude_ids=None, user_id=None):
            books = [BookSummary(**b) for b in mock_books]
            return books, len(books)

        with patch("app.services.recommendation.search_books", side_effect=mock_search):
            resp = client.get("/api/recommendations", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0

    def test_requires_auth(self, client):
        """Unauthenticated requests are rejected."""
        resp = client.get("/api/recommendations")
        assert resp.status_code == 401

    def test_pagination(self, client, auth_headers):
        """Pagination parameters are respected."""
        mock_books = [
            {
                "google_book_id": f"page_{i}",
                "title": f"Book {i}",
                "authors": [],
                "thumbnail": "",
                "categories": [],
                "average_rating": None,
                "ratings_count": None,
                "description": "",
                "page_count": None,
                "published_date": None,
                "publisher": None,
            }
            for i in range(3)
        ]

        async def mock_search(category, page=1, page_size=20, exclude_ids=None, user_id=None):
            books = [BookSummary(**b) for b in mock_books]
            return books, len(books)

        with patch("app.services.recommendation.search_books", side_effect=mock_search):
            resp = client.get(
                "/api/recommendations?page=1&page_size=2", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["page"] == 1
        assert data["page_size"] == 2


class TestCacheInvalidation:
    """Tests for recommendation cache invalidation on swipe."""

    def test_swipe_invalidates_cache(self, client, auth_headers):
        """Creating a swipe event invalidates the recommendation cache."""
        with patch("app.services.recommendation.cache_delete", new_callable=AsyncMock) as mock_del:
            resp = client.post("/api/swipe-events", json={
                "google_book_id": "cache_test",
                "action": "like",
            }, headers=auth_headers)
            assert resp.status_code == 201
            assert mock_del.call_count > 0


class TestBackgroundWorker:
    """Tests for the background preference computation worker."""

    def test_compute_and_store_preferences(self):
        """Worker correctly computes and stores preference scores."""
        from app.services.recommendation import compute_and_store_preferences

        db = TestingSessionLocal()
        try:
            # Create a user
            from app.models import User
            from app.services.auth import hash_password
            user = User(email="worker_test@example.com", hashed_password=hash_password(VALID_TEST_PASSWORD))
            db.add(user)
            db.commit()
            db.refresh(user)

            # Add swipe events
            for i in range(3):
                db.add(SwipeEvent(
                    user_id=user.id,
                    google_book_id=f"worker_book_{i}",
                    action="like",
                    genre="Sci-Fi",
                    author="Isaac Asimov",
                    category="Science Fiction",
                ))
            db.commit()

            # Run the computation
            compute_and_store_preferences(db, user.id)

            # Verify preferences were stored
            pref = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
            assert pref is not None
            import json
            genres = json.loads(pref.genre_scores)
            assert "Sci-Fi" in genres
            assert genres["Sci-Fi"] == 1.0
        finally:
            db.close()

    def test_compute_no_events(self):
        """Worker skips users with no swipe events."""
        from app.services.recommendation import compute_and_store_preferences

        db = TestingSessionLocal()
        try:
            from app.models import User
            from app.services.auth import hash_password
            user = User(email="noevents@example.com", hashed_password=hash_password(VALID_TEST_PASSWORD))
            db.add(user)
            db.commit()
            db.refresh(user)

            compute_and_store_preferences(db, user.id)

            pref = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
            assert pref is None
        finally:
            db.close()
