"""Tests for the reviews & ratings feature."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import User
from app.services.auth import create_access_token, hash_password

from .conftest import VALID_TEST_PASSWORD, TestingSessionLocal


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def user_a(db_session):
    user = User(email="usera@test.com", hashed_password=hash_password(VALID_TEST_PASSWORD))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def user_b(db_session):
    user = User(email="userb@test.com", hashed_password=hash_password(VALID_TEST_PASSWORD))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def headers_a(user_a):
    token = create_access_token(user_a.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def headers_b(user_b):
    token = create_access_token(user_b.id)
    return {"Authorization": f"Bearer {token}"}


BOOK_ID = "test_book_123"


class TestCreateReview:
    def test_create_review(self, client, headers_a):
        resp = client.post(
            f"/api/books/{BOOK_ID}/reviews",
            json={"rating": 5, "review_text": "Great book!"},
            headers=headers_a,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["rating"] == 5
        assert data["review_text"] == "Great book!"
        assert data["google_book_id"] == BOOK_ID

    def test_upsert_review(self, client, headers_a):
        """Second review for same book updates the existing one."""
        client.post(
            f"/api/books/{BOOK_ID}/reviews",
            json={"rating": 3, "review_text": "OK"},
            headers=headers_a,
        )
        resp = client.post(
            f"/api/books/{BOOK_ID}/reviews",
            json={"rating": 5, "review_text": "Changed my mind!"},
            headers=headers_a,
        )
        assert resp.status_code == 201
        assert resp.json()["rating"] == 5
        assert resp.json()["review_text"] == "Changed my mind!"

    def test_invalid_rating(self, client, headers_a):
        resp = client.post(
            f"/api/books/{BOOK_ID}/reviews",
            json={"rating": 0},
            headers=headers_a,
        )
        assert resp.status_code == 422

    def test_rating_too_high(self, client, headers_a):
        resp = client.post(
            f"/api/books/{BOOK_ID}/reviews",
            json={"rating": 6},
            headers=headers_a,
        )
        assert resp.status_code == 422

    def test_unauthenticated(self, client):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 5})
        assert resp.status_code == 401


class TestGetReviews:
    def test_get_book_reviews(self, client, headers_a, headers_b):
        client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 5, "review_text": "A"}, headers=headers_a)
        client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 3, "review_text": "B"}, headers=headers_b)

        resp = client.get(f"/api/books/{BOOK_ID}/reviews", headers=headers_a)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["average_rating"] is not None
        assert data["total_ratings"] == 2

    def test_pagination(self, client, headers_a):
        client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 4}, headers=headers_a)
        resp = client.get(f"/api/books/{BOOK_ID}/reviews?page=1&page_size=1", headers=headers_a)
        assert resp.status_code == 200
        assert len(resp.json()["reviews"]) <= 1

    def test_sort_by_helpful(self, client, headers_a):
        client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 4}, headers=headers_a)
        resp = client.get(f"/api/books/{BOOK_ID}/reviews?sort_by=helpful", headers=headers_a)
        assert resp.status_code == 200

    def test_empty_reviews(self, client, headers_a):
        resp = client.get("/api/books/nonexistent/reviews", headers=headers_a)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestUpdateReview:
    def test_update_own_review(self, client, headers_a):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 3}, headers=headers_a)
        review_id = resp.json()["id"]

        resp = client.put(f"/api/reviews/{review_id}", json={"rating": 5}, headers=headers_a)
        assert resp.status_code == 200
        assert resp.json()["rating"] == 5

    def test_cannot_update_others_review(self, client, headers_a, headers_b):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 3}, headers=headers_a)
        review_id = resp.json()["id"]

        resp = client.put(f"/api/reviews/{review_id}", json={"rating": 1}, headers=headers_b)
        assert resp.status_code == 403

    def test_update_nonexistent(self, client, headers_a):
        resp = client.put("/api/reviews/99999", json={"rating": 5}, headers=headers_a)
        assert resp.status_code == 404


class TestDeleteReview:
    def test_delete_own_review(self, client, headers_a):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 3}, headers=headers_a)
        review_id = resp.json()["id"]

        resp = client.delete(f"/api/reviews/{review_id}", headers=headers_a)
        assert resp.status_code == 200

    def test_cannot_delete_others_review(self, client, headers_a, headers_b):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 3}, headers=headers_a)
        review_id = resp.json()["id"]

        resp = client.delete(f"/api/reviews/{review_id}", headers=headers_b)
        assert resp.status_code == 403

    def test_admin_can_delete_any_review(self, client, headers_a, admin_headers):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 3}, headers=headers_a)
        review_id = resp.json()["id"]

        resp = client.delete(f"/api/reviews/{review_id}", headers=admin_headers)
        assert resp.status_code == 200


class TestRatingStats:
    def test_get_rating_stats(self, client, headers_a, headers_b):
        client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 5}, headers=headers_a)
        client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 3}, headers=headers_b)

        resp = client.get(f"/api/books/{BOOK_ID}/ratings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["average_rating"] == 4.0
        assert data["total_ratings"] == 2
        assert "5" in data["rating_distribution"]

    def test_no_ratings(self, client):
        resp = client.get("/api/books/nonexistent/ratings")
        assert resp.status_code == 200
        assert resp.json()["average_rating"] is None


class TestVoting:
    def test_vote_helpful(self, client, headers_a, headers_b):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 5}, headers=headers_a)
        review_id = resp.json()["id"]

        resp = client.post(f"/api/reviews/{review_id}/vote", headers=headers_b)
        assert resp.status_code == 201

    def test_cannot_self_vote(self, client, headers_a):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 5}, headers=headers_a)
        review_id = resp.json()["id"]

        resp = client.post(f"/api/reviews/{review_id}/vote", headers=headers_a)
        assert resp.status_code == 409

    def test_duplicate_vote(self, client, headers_a, headers_b):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 5}, headers=headers_a)
        review_id = resp.json()["id"]

        client.post(f"/api/reviews/{review_id}/vote", headers=headers_b)
        resp = client.post(f"/api/reviews/{review_id}/vote", headers=headers_b)
        assert resp.status_code == 409

    def test_remove_vote(self, client, headers_a, headers_b):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 5}, headers=headers_a)
        review_id = resp.json()["id"]

        client.post(f"/api/reviews/{review_id}/vote", headers=headers_b)
        resp = client.delete(f"/api/reviews/{review_id}/vote", headers=headers_b)
        assert resp.status_code == 200

    def test_vote_nonexistent_review(self, client, headers_a):
        resp = client.post("/api/reviews/99999/vote", headers=headers_a)
        assert resp.status_code == 404

    def test_helpful_count_increments(self, client, headers_a, headers_b):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 5}, headers=headers_a)
        review_id = resp.json()["id"]

        client.post(f"/api/reviews/{review_id}/vote", headers=headers_b)

        resp = client.get(f"/api/books/{BOOK_ID}/reviews", headers=headers_a)
        review = resp.json()["reviews"][0]
        assert review["helpful_count"] == 1

    def test_user_has_voted_flag(self, client, headers_a, headers_b):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 5}, headers=headers_a)
        review_id = resp.json()["id"]
        client.post(f"/api/reviews/{review_id}/vote", headers=headers_b)

        # user_b should see user_has_voted=True
        resp = client.get(f"/api/books/{BOOK_ID}/reviews", headers=headers_b)
        review = resp.json()["reviews"][0]
        assert review["user_has_voted"] is True

        # user_a should see user_has_voted=False
        resp = client.get(f"/api/books/{BOOK_ID}/reviews", headers=headers_a)
        review = resp.json()["reviews"][0]
        assert review["user_has_voted"] is False


class TestAdminModeration:
    def test_flag_review(self, client, headers_a, admin_headers):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 1, "review_text": "Spam"}, headers=headers_a)
        review_id = resp.json()["id"]

        resp = client.post(f"/api/admin/reviews/{review_id}/flag", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["is_flagged"] is True

    def test_flagged_review_hidden(self, client, headers_a, admin_headers):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 1}, headers=headers_a)
        review_id = resp.json()["id"]
        client.post(f"/api/admin/reviews/{review_id}/flag", headers=admin_headers)

        resp = client.get(f"/api/books/{BOOK_ID}/reviews", headers=headers_a)
        assert resp.json()["total"] == 0

    def test_unflag_review(self, client, headers_a, admin_headers):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 1}, headers=headers_a)
        review_id = resp.json()["id"]
        client.post(f"/api/admin/reviews/{review_id}/flag", headers=admin_headers)
        resp = client.post(f"/api/admin/reviews/{review_id}/unflag", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["is_flagged"] is False

    def test_non_admin_cannot_flag(self, client, headers_a):
        resp = client.post(f"/api/books/{BOOK_ID}/reviews", json={"rating": 1}, headers=headers_a)
        review_id = resp.json()["id"]

        resp = client.post(f"/api/admin/reviews/{review_id}/flag", headers=headers_a)
        assert resp.status_code == 403
