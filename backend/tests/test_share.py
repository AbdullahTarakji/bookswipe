"""Tests for the share / deep links feature."""


import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import BookList, User
from app.services.share import render_og_html, share_book, share_list, share_user
from app.schemas import OGMetadata

from tests.conftest import VALID_TEST_PASSWORD, TestingSessionLocal


@pytest.fixture()
def client():
    return TestClient(app)


def _register(client, email="sharer@example.com"):
    """Register a user and return (profile_dict, headers)."""
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": VALID_TEST_PASSWORD,
    })
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    # Get user_id from profile endpoint
    profile = client.get("/api/profile", headers=headers).json()
    return profile, headers


@pytest.fixture()
def auth_user(client):
    return _register(client)


@pytest.fixture()
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Unit tests for share service ---


class TestShareService:
    def test_share_book_generates_url_and_og(self, db):
        resp = share_book(
            db,
            google_book_id="abc123",
            title="Test Book",
            authors=["Author A"],
            thumbnail="https://example.com/thumb.jpg",
            description="A great book.",
        )
        assert "/books/abc123" in resp.url
        assert resp.short_url is not None
        assert "/s/" in resp.short_url
        assert resp.og.og_title == "Test Book"
        assert resp.og.og_type == "book"
        assert resp.og.og_image == "https://example.com/thumb.jpg"

    def test_share_book_reuses_short_code(self, db):
        r1 = share_book(db, "abc123", "T", ["A"], None)
        r2 = share_book(db, "abc123", "T", ["A"], None)
        assert r1.short_url == r2.short_url

    def test_share_list(self, db):
        user = db.query(User).first()
        if not user:
            from app.services.auth import hash_password
            user = User(email="listowner@test.com", hashed_password=hash_password(VALID_TEST_PASSWORD))
            db.add(user)
            db.commit()
            db.refresh(user)

        bl = BookList(user_id=user.id, name="My List", description="Cool books")
        db.add(bl)
        db.commit()
        db.refresh(bl)

        resp = share_list(db, bl, "listowner")
        assert f"/lists/{bl.id}" in resp.url
        assert resp.og.og_title == "My List"

    def test_share_user(self, db):
        user = db.query(User).first()
        if not user:
            from app.services.auth import hash_password
            user = User(email="profile@test.com", hashed_password=hash_password(VALID_TEST_PASSWORD))
            db.add(user)
            db.commit()
            db.refresh(user)

        resp = share_user(db, user, None)
        assert f"/users/{user.id}" in resp.url
        assert resp.og.og_type == "profile"

    def test_render_og_html_contains_meta_tags(self):
        og = OGMetadata(
            og_title="Test",
            og_description="Desc",
            og_image="https://img.example.com/a.jpg",
            og_type="book",
            og_url="https://bookswipe.app/books/abc",
        )
        html = render_og_html(og)
        assert 'og:title' in html
        assert 'og:description' in html
        assert 'og:image' in html
        assert 'og:type' in html
        assert 'twitter:card' in html
        assert "Test" in html

    def test_render_og_html_no_image(self):
        og = OGMetadata(og_title="T", og_description="D", og_url="https://x.com")
        html = render_og_html(og)
        assert 'og:image' not in html


# --- API endpoint tests ---


class TestShareEndpoints:
    def test_share_book_endpoint(self, client, auth_user, mock_google_book_detail):
        _, headers = auth_user
        resp = client.get("/api/share/books/book_1", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "url" in data
        assert "og" in data
        assert data["og"]["og_title"] == "Test Book One"

    def test_share_book_requires_auth(self, client, mock_google_book_detail):
        resp = client.get("/api/share/books/book_1")
        assert resp.status_code in (401, 403)

    def test_share_list_endpoint(self, client, auth_user, db):
        data, headers = auth_user
        user_id = data["user_id"]

        bl = BookList(user_id=user_id, name="Shared List", is_public=True)
        db.add(bl)
        db.commit()
        db.refresh(bl)

        resp = client.get(f"/api/share/lists/{bl.id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["og"]["og_title"] == "Shared List"

    def test_share_list_not_found(self, client, auth_user):
        _, headers = auth_user
        resp = client.get("/api/share/lists/99999", headers=headers)
        assert resp.status_code == 404

    def test_share_user_endpoint(self, client, auth_user):
        data, headers = auth_user
        user_id = data["user_id"]
        resp = client.get(f"/api/share/users/{user_id}", headers=headers)
        assert resp.status_code == 200
        assert "og" in resp.json()

    def test_share_user_not_found(self, client, auth_user):
        _, headers = auth_user
        resp = client.get("/api/share/users/99999", headers=headers)
        assert resp.status_code == 404


# --- OG page tests (bot vs human) ---


class TestOGPages:
    BOT_UA = "Twitterbot/1.0"
    HUMAN_UA = "Mozilla/5.0"

    def test_book_og_page_bot(self, client, mock_google_book_detail):
        resp = client.get(
            "/books/book_1",
            headers={"User-Agent": self.BOT_UA},
            follow_redirects=False,
        )
        assert resp.status_code == 200
        assert "og:title" in resp.text

    def test_book_og_page_human_redirects(self, client):
        resp = client.get(
            "/books/book_1",
            headers={"User-Agent": self.HUMAN_UA},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/book/book_1" in resp.headers["location"]

    def test_user_og_page_bot(self, client, auth_user):
        data, _ = auth_user
        user_id = data["user_id"]
        resp = client.get(
            f"/users/{user_id}",
            headers={"User-Agent": self.BOT_UA},
            follow_redirects=False,
        )
        assert resp.status_code == 200
        assert "og:title" in resp.text

    def test_user_og_page_human_redirects(self, client, auth_user):
        data, _ = auth_user
        user_id = data["user_id"]
        resp = client.get(
            f"/users/{user_id}",
            headers={"User-Agent": self.HUMAN_UA},
            follow_redirects=False,
        )
        assert resp.status_code == 302

    def test_list_og_page_bot(self, client, auth_user, db):
        data, _ = auth_user
        user_id = data["user_id"]
        bl = BookList(user_id=user_id, name="Bot List", is_public=True)
        db.add(bl)
        db.commit()
        db.refresh(bl)

        resp = client.get(
            f"/lists/{bl.id}",
            headers={"User-Agent": self.BOT_UA},
            follow_redirects=False,
        )
        assert resp.status_code == 200
        assert "og:title" in resp.text


# --- Short link tests ---


class TestShortLinks:
    def test_short_link_resolves_for_human(self, client, auth_user, mock_google_book_detail):
        _, headers = auth_user
        # Generate a share link first
        resp = client.get("/api/share/books/book_1", headers=headers)
        short_url = resp.json()["short_url"]
        short_code = short_url.split("/s/")[-1]

        resp = client.get(
            f"/s/{short_code}",
            headers={"User-Agent": "Mozilla/5.0"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/book/book_1" in resp.headers["location"]

    def test_short_link_resolves_for_bot(self, client, auth_user, mock_google_book_detail):
        _, headers = auth_user
        resp = client.get("/api/share/books/book_1", headers=headers)
        short_code = resp.json()["short_url"].split("/s/")[-1]

        resp = client.get(
            f"/s/{short_code}",
            headers={"User-Agent": "Twitterbot/1.0"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/books/book_1" in resp.headers["location"]

    def test_short_link_not_found(self, client):
        resp = client.get("/s/nonexistent", follow_redirects=False)
        assert resp.status_code == 404
