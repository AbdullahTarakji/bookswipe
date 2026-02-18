"""Tests for book reviews: CRUD, permissions, voting, pagination, admin moderation."""

from tests.conftest import VALID_TEST_PASSWORD


# --- Helpers ---


def _register(client, email="reviewer@example.com"):
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": VALID_TEST_PASSWORD,
    })
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    return data, headers


def _make_admin(db_session, email):
    from app.models import User
    user = db_session.query(User).filter(User.email == email).first()
    user.role = "admin"
    db_session.commit()


def _create_review(client, headers, book_id="book_1", rating=4, text="Great book!"):
    return client.post(f"/api/books/{book_id}/reviews", headers=headers, json={
        "rating": rating,
        "review_text": text,
    })


# --- Create Review ---


def test_create_review(client):
    _, headers = _register(client)
    resp = _create_review(client, headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 4
    assert data["review_text"] == "Great book!"
    assert data["google_book_id"] == "book_1"
    assert data["username"] == "reviewer"


def test_create_review_rating_validation(client):
    _, headers = _register(client)
    resp = client.post("/api/books/book_1/reviews", headers=headers, json={
        "rating": 0,
        "review_text": "Bad",
    })
    assert resp.status_code == 422

    resp = client.post("/api/books/book_1/reviews", headers=headers, json={
        "rating": 6,
        "review_text": "Bad",
    })
    assert resp.status_code == 422


def test_upsert_review(client):
    """Creating a second review for the same book updates the existing one."""
    _, headers = _register(client)
    resp1 = _create_review(client, headers, rating=3, text="OK")
    assert resp1.status_code == 201
    review_id = resp1.json()["id"]

    resp2 = _create_review(client, headers, rating=5, text="Actually amazing!")
    assert resp2.status_code == 201
    assert resp2.json()["id"] == review_id
    assert resp2.json()["rating"] == 5
    assert resp2.json()["review_text"] == "Actually amazing!"


# --- Get Reviews ---


def test_get_book_reviews(client):
    _, h1 = _register(client, "user1@example.com")
    _, h2 = _register(client, "user2@example.com")
    _create_review(client, h1, rating=4, text="Good")
    _create_review(client, h2, rating=5, text="Excellent")

    resp = client.get("/api/books/book_1/reviews", headers=h1)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["total_ratings"] == 2
    assert data["average_rating"] == 4.5
    assert len(data["reviews"]) == 2


def test_get_reviews_pagination(client):
    _, h1 = _register(client, "user1@example.com")
    _, h2 = _register(client, "user2@example.com")
    _, h3 = _register(client, "user3@example.com")
    _create_review(client, h1, rating=3, text="A")
    _create_review(client, h2, rating=4, text="B")
    _create_review(client, h3, rating=5, text="C")

    resp = client.get("/api/books/book_1/reviews?page=1&page_size=2", headers=h1)
    data = resp.json()
    assert data["total"] == 3
    assert len(data["reviews"]) == 2

    resp2 = client.get("/api/books/book_1/reviews?page=2&page_size=2", headers=h1)
    data2 = resp2.json()
    assert len(data2["reviews"]) == 1


def test_get_reviews_sort_helpful(client):
    _, h1 = _register(client, "user1@example.com")
    _, h2 = _register(client, "user2@example.com")
    _, h3 = _register(client, "user3@example.com")
    _create_review(client, h1, rating=3, text="Meh")
    resp2 = _create_review(client, h2, rating=5, text="Best ever")
    review_id = resp2.json()["id"]

    # h1 and h3 vote on h2's review
    client.post(f"/api/reviews/{review_id}/helpful", headers=h1)
    client.post(f"/api/reviews/{review_id}/helpful", headers=h3)

    resp = client.get("/api/books/book_1/reviews?sort=helpful", headers=h1)
    data = resp.json()
    assert data["reviews"][0]["id"] == review_id
    assert data["reviews"][0]["helpful_count"] == 2


# --- Update Review ---


def test_update_review(client):
    _, headers = _register(client)
    resp = _create_review(client, headers)
    review_id = resp.json()["id"]

    resp = client.put(f"/api/reviews/{review_id}", headers=headers, json={
        "rating": 2,
        "review_text": "Changed my mind",
    })
    assert resp.status_code == 200
    assert resp.json()["rating"] == 2
    assert resp.json()["review_text"] == "Changed my mind"


def test_update_other_users_review_forbidden(client):
    _, h1 = _register(client, "user1@example.com")
    _, h2 = _register(client, "user2@example.com")
    resp = _create_review(client, h1)
    review_id = resp.json()["id"]

    resp = client.put(f"/api/reviews/{review_id}", headers=h2, json={"rating": 1})
    assert resp.status_code == 403


# --- Delete Review ---


def test_delete_own_review(client):
    _, headers = _register(client)
    resp = _create_review(client, headers)
    review_id = resp.json()["id"]

    resp = client.delete(f"/api/reviews/{review_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "Review deleted"

    # Verify it's gone
    resp = client.get("/api/books/book_1/reviews", headers=headers)
    assert resp.json()["total"] == 0


def test_delete_other_users_review_forbidden(client):
    _, h1 = _register(client, "user1@example.com")
    _, h2 = _register(client, "user2@example.com")
    resp = _create_review(client, h1)
    review_id = resp.json()["id"]

    resp = client.delete(f"/api/reviews/{review_id}", headers=h2)
    assert resp.status_code == 403


# --- Helpful Votes ---


def test_vote_helpful(client):
    _, h1 = _register(client, "user1@example.com")
    _, h2 = _register(client, "user2@example.com")
    resp = _create_review(client, h1)
    review_id = resp.json()["id"]

    resp = client.post(f"/api/reviews/{review_id}/helpful", headers=h2)
    assert resp.status_code == 201

    # Check user_has_voted
    resp = client.get("/api/books/book_1/reviews", headers=h2)
    review = [r for r in resp.json()["reviews"] if r["id"] == review_id][0]
    assert review["helpful_count"] == 1
    assert review["user_has_voted"] is True


def test_cannot_vote_own_review(client):
    _, headers = _register(client)
    resp = _create_review(client, headers)
    review_id = resp.json()["id"]

    resp = client.post(f"/api/reviews/{review_id}/helpful", headers=headers)
    assert resp.status_code == 409


def test_cannot_double_vote(client):
    _, h1 = _register(client, "user1@example.com")
    _, h2 = _register(client, "user2@example.com")
    resp = _create_review(client, h1)
    review_id = resp.json()["id"]

    client.post(f"/api/reviews/{review_id}/helpful", headers=h2)
    resp = client.post(f"/api/reviews/{review_id}/helpful", headers=h2)
    assert resp.status_code == 409


def test_remove_helpful_vote(client):
    _, h1 = _register(client, "user1@example.com")
    _, h2 = _register(client, "user2@example.com")
    resp = _create_review(client, h1)
    review_id = resp.json()["id"]

    client.post(f"/api/reviews/{review_id}/helpful", headers=h2)
    resp = client.delete(f"/api/reviews/{review_id}/helpful", headers=h2)
    assert resp.status_code == 200

    resp = client.get("/api/books/book_1/reviews", headers=h1)
    review = resp.json()["reviews"][0]
    assert review["helpful_count"] == 0


# --- Admin Moderation ---


def test_admin_flag_review(client, db_session):
    _, h1 = _register(client, "user1@example.com")
    _, h_admin = _register(client, "admin@example.com")
    _make_admin(db_session, "admin@example.com")

    resp = _create_review(client, h1)
    review_id = resp.json()["id"]

    resp = client.post(f"/api/admin/reviews/{review_id}/flag", headers=h_admin, json={
        "reason": "Inappropriate content",
    })
    assert resp.status_code == 200
    assert resp.json()["is_flagged"] is True

    # Flagged reviews hidden from normal listing
    resp = client.get("/api/books/book_1/reviews", headers=h1)
    assert resp.json()["total"] == 0


def test_admin_unflag_review(client, db_session):
    _, h1 = _register(client, "user1@example.com")
    _, h_admin = _register(client, "admin@example.com")
    _make_admin(db_session, "admin@example.com")

    resp = _create_review(client, h1)
    review_id = resp.json()["id"]

    client.post(f"/api/admin/reviews/{review_id}/flag", headers=h_admin, json={"reason": "Spam"})
    resp = client.delete(f"/api/admin/reviews/{review_id}/flag", headers=h_admin)
    assert resp.status_code == 200
    assert resp.json()["is_flagged"] is False


def test_admin_delete_review(client, db_session):
    _, h1 = _register(client, "user1@example.com")
    _, h_admin = _register(client, "admin@example.com")
    _make_admin(db_session, "admin@example.com")

    resp = _create_review(client, h1)
    review_id = resp.json()["id"]

    resp = client.delete(f"/api/admin/reviews/{review_id}", headers=h_admin)
    assert resp.status_code == 200


def test_non_admin_cannot_flag(client):
    _, h1 = _register(client, "user1@example.com")
    _, h2 = _register(client, "user2@example.com")
    resp = _create_review(client, h1)
    review_id = resp.json()["id"]

    resp = client.post(f"/api/admin/reviews/{review_id}/flag", headers=h2, json={"reason": "test"})
    assert resp.status_code == 403


# --- Edge Cases ---


def test_review_not_found(client):
    _, headers = _register(client)
    resp = client.put("/api/reviews/99999", headers=headers, json={"rating": 3})
    assert resp.status_code == 404

    resp = client.delete("/api/reviews/99999", headers=headers)
    assert resp.status_code == 404


def test_vote_on_nonexistent_review(client):
    _, headers = _register(client)
    resp = client.post("/api/reviews/99999/helpful", headers=headers)
    assert resp.status_code == 404


def test_empty_reviews_for_book(client):
    _, headers = _register(client)
    resp = client.get("/api/books/nonexistent_book/reviews", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["average_rating"] is None
    assert data["reviews"] == []


def test_review_with_empty_text(client):
    _, headers = _register(client)
    resp = client.post("/api/books/book_1/reviews", headers=headers, json={
        "rating": 5,
        "review_text": "",
    })
    assert resp.status_code == 201
    assert resp.json()["review_text"] == ""
