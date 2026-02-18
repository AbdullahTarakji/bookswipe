"""Tests for the analytics dashboard endpoints."""

import datetime

import pytest
from fastapi.testclient import TestClient

from app.models import LikedBook, SkippedBook, SwipeEvent, User
from tests.conftest import VALID_TEST_PASSWORD


class TestAnalyticsPermissions:
    """Ensure analytics endpoints require admin access."""

    ENDPOINTS = [
        "/api/admin/analytics/detailed",
        "/api/admin/analytics/engagement",
        "/api/admin/analytics/swipes",
        "/api/admin/analytics/popular-books",
        "/api/admin/analytics/retention",
        "/api/admin/analytics/categories",
    ]

    def test_unauthenticated_returns_401(self, client: TestClient):
        for endpoint in self.ENDPOINTS:
            resp = client.get(endpoint)
            assert resp.status_code == 401, f"{endpoint} should require auth"

    def test_non_admin_returns_401(self, client: TestClient, auth_headers):
        """Non-admin users get 401 (AuthError maps to 401 in this app)."""
        for endpoint in self.ENDPOINTS:
            resp = client.get(endpoint, headers=auth_headers)
            assert resp.status_code == 401, f"{endpoint} should require admin"

    def test_admin_returns_200(self, client: TestClient, admin_headers):
        for endpoint in self.ENDPOINTS:
            resp = client.get(endpoint, headers=admin_headers)
            assert resp.status_code == 200, f"{endpoint} failed: {resp.text}"


class TestDetailedAnalytics:
    """Test the /detailed endpoint returns full analytics."""

    def test_returns_all_sections(self, client: TestClient, admin_headers):
        resp = client.get("/api/admin/analytics/detailed", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "engagement" in data
        assert "swipes" in data
        assert "popular_books" in data
        assert "retention" in data
        assert "categories" in data

    def test_engagement_structure(self, client: TestClient, admin_headers):
        resp = client.get("/api/admin/analytics/detailed", headers=admin_headers)
        eng = resp.json()["engagement"]
        assert "dau" in eng
        assert "wau" in eng
        assert "mau" in eng
        assert "signups_over_time" in eng
        assert isinstance(eng["dau"], int)

    def test_swipes_structure(self, client: TestClient, admin_headers):
        resp = client.get("/api/admin/analytics/detailed", headers=admin_headers)
        sw = resp.json()["swipes"]
        assert "total_swipes" in sw
        assert "like_ratio" in sw
        assert "skip_ratio" in sw
        assert "swipes_per_user_avg" in sw
        assert "swipes_over_time" in sw


class TestEngagementEndpoint:
    """Test /engagement endpoint."""

    def test_returns_engagement_metrics(self, client: TestClient, admin_headers):
        resp = client.get("/api/admin/analytics/engagement", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["dau"] >= 0
        assert data["wau"] >= 0
        assert data["mau"] >= 0


class TestSwipesEndpoint:
    """Test /swipes endpoint."""

    def test_empty_database(self, client: TestClient, admin_headers):
        resp = client.get("/api/admin/analytics/swipes", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_swipes"] == 0
        assert data["like_ratio"] == 0
        assert data["swipes_per_user_avg"] == 0

    def test_with_swipe_data(self, client: TestClient, admin_headers, db_session, admin_user):
        # Create swipe events
        for i in range(5):
            db_session.add(SwipeEvent(
                user_id=admin_user.id,
                google_book_id=f"book_{i}",
                action="like" if i < 3 else "skip",
                genre="Fiction",
                category="Fiction",
            ))
        db_session.commit()

        resp = client.get("/api/admin/analytics/swipes", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_swipes"] == 5
        assert data["total_likes"] == 3
        assert data["total_skips"] == 2
        assert data["like_ratio"] == 60.0
        assert data["swipes_per_user_avg"] == 5.0


class TestPopularBooksEndpoint:
    """Test /popular-books endpoint."""

    def test_empty_database(self, client: TestClient, admin_headers):
        resp = client.get("/api/admin/analytics/popular-books", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["most_liked"] == []
        assert data["most_swiped"] == []
        assert data["trending_this_week"] == []

    def test_with_liked_books(self, client: TestClient, admin_headers, db_session, admin_user):
        for i in range(3):
            db_session.add(LikedBook(
                user_id=admin_user.id,
                google_book_id=f"book_{i}",
                title=f"Book {i}",
                authors=f"Author {i}",
                thumbnail=f"https://example.com/{i}.jpg",
            ))
        db_session.commit()

        resp = client.get("/api/admin/analytics/popular-books", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["most_liked"]) == 3
        assert data["most_liked"][0]["title"] == "Book 0"


class TestRetentionEndpoint:
    """Test /retention endpoint."""

    def test_returns_cohorts(self, client: TestClient, admin_headers):
        resp = client.get("/api/admin/analytics/retention", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "cohorts" in data
        assert isinstance(data["cohorts"], list)
        assert len(data["cohorts"]) == 4  # default 4 weeks


class TestCategoriesEndpoint:
    """Test /categories endpoint."""

    def test_empty_database(self, client: TestClient, admin_headers):
        resp = client.get("/api/admin/analytics/categories", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["likes_by_category"] == []
        assert data["most_active_categories"] == []

    def test_with_category_data(self, client: TestClient, admin_headers, db_session, admin_user):
        categories = ["Fiction", "Science", "Fiction", "Romance", "Fiction"]
        for i, cat in enumerate(categories):
            db_session.add(SwipeEvent(
                user_id=admin_user.id,
                google_book_id=f"book_{i}",
                action="like",
                genre=cat,
                category=cat,
            ))
        db_session.commit()

        resp = client.get("/api/admin/analytics/categories", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["likes_by_category"]) > 0
        # Fiction should be first (3 likes)
        assert data["likes_by_category"][0]["category"] == "Fiction"
        assert data["likes_by_category"][0]["count"] == 3
