"""Tests for search functionality: unified search, history, autocomplete, trending."""

from unittest.mock import AsyncMock, patch

from tests.conftest import VALID_TEST_PASSWORD


# --- Helpers ---


def _register(client, email="user1@example.com"):
    """Register a user and return (tokens_dict, auth_headers)."""
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": VALID_TEST_PASSWORD,
    })
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    return data, headers


def _register_two(client):
    """Register two users and return their auth headers."""
    _, h1 = _register(client, "alice@example.com")
    _, h2 = _register(client, "bob@example.com")
    return h1, h2


# --- Search History Tests ---


def test_search_history_empty(client):
    _, headers = _register(client)
    resp = client.get("/api/search/history", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_search_history_after_search(client):
    _, headers = _register(client)
    # Perform a search (mock Google Books)
    with patch("app.services.search.search_books_google", new_callable=AsyncMock) as mock_gb:
        mock_gb.return_value = ([], 0)
        resp = client.get("/api/search", params={"q": "python"}, headers=headers)
        assert resp.status_code == 200

    # Check history
    resp = client.get("/api/search/history", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["query"] == "python"
    assert data["items"][0]["search_type"] == "all"


def test_clear_search_history(client):
    _, headers = _register(client)
    with patch("app.services.search.search_books_google", new_callable=AsyncMock) as mock_gb:
        mock_gb.return_value = ([], 0)
        client.get("/api/search", params={"q": "python"}, headers=headers)
        client.get("/api/search", params={"q": "flutter"}, headers=headers)

    resp = client.delete("/api/search/history", headers=headers)
    assert resp.status_code == 200
    assert "2" in resp.json()["message"]

    resp = client.get("/api/search/history", headers=headers)
    assert resp.json()["total"] == 0


def test_delete_single_history_item(client):
    _, headers = _register(client)
    with patch("app.services.search.search_books_google", new_callable=AsyncMock) as mock_gb:
        mock_gb.return_value = ([], 0)
        resp = client.get("/api/search", params={"q": "python"}, headers=headers)
        assert resp.status_code == 200

        history_resp = client.get("/api/search/history", headers=headers)
        assert history_resp.status_code == 200
        history = history_resp.json()
        item_id = history["items"][0]["id"]

        resp = client.delete(f"/api/search/history/{item_id}", headers=headers)
        assert resp.status_code == 200

        resp = client.get("/api/search/history", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


def test_delete_nonexistent_history_item(client):
    _, headers = _register(client)
    resp = client.delete("/api/search/history/99999", headers=headers)
    assert resp.status_code == 404


# --- Unified Search Tests ---


def test_unified_search_all(client):
    h1, h2 = _register_two(client)
    with patch("app.services.search.search_books_google", new_callable=AsyncMock) as mock_gb:
        mock_gb.return_value = ([{
            "google_book_id": "abc123",
            "title": "Test Book",
            "authors": ["Author"],
            "thumbnail": "",
            "categories": [],
            "average_rating": 4.0,
            "published_date": "2023",
        }], 1)
        # Patch to return BookSearchResult objects
        from app.schemas import BookSearchResult
        mock_gb.return_value = ([BookSearchResult(
            google_book_id="abc123",
            title="Test Book",
            authors=["Author"],
            thumbnail="",
            categories=[],
            average_rating=4.0,
            published_date="2023",
        )], 1)

        resp = client.get("/api/search", params={"q": "alice"}, headers=h2)
        assert resp.status_code == 200
        data = resp.json()
        assert "books" in data
        assert "users" in data
        assert "lists" in data


def test_search_users_only(client):
    h1, h2 = _register_two(client)
    resp = client.get("/api/search", params={"q": "alice", "search_type": "users"}, headers=h2)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["users"]) >= 1
    assert data["users"][0]["username"] == "alice"
    assert data["books"] == []
    assert data["lists"] == []


def test_search_lists_only(client):
    _, headers = _register(client)
    # Create a public list
    client.post("/api/book-lists", json={"name": "My Python Books", "description": "Great reads"}, headers=headers)

    resp = client.get("/api/search", params={"q": "Python", "search_type": "lists"}, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["lists"]) >= 1
    assert "Python" in data["lists"][0]["name"]


def test_search_with_filters(client):
    _, headers = _register(client)
    with patch("app.services.search.search_books_google", new_callable=AsyncMock) as mock_gb:
        mock_gb.return_value = ([], 0)
        resp = client.get("/api/search", params={
            "q": "fiction",
            "search_type": "books",
            "category": "fiction",
            "min_rating": 4.0,
            "year_from": 2020,
        }, headers=headers)
        assert resp.status_code == 200
        # Verify filters were passed
        call_args = mock_gb.call_args
        filters = call_args[1].get("filters") or call_args[0][1]
        assert filters.category == "fiction"
        assert filters.min_rating == 4.0
        assert filters.year_from == 2020


def test_search_requires_auth(client):
    resp = client.get("/api/search", params={"q": "test"})
    assert resp.status_code == 401


def test_search_empty_query_rejected(client):
    _, headers = _register(client)
    resp = client.get("/api/search", params={"q": ""}, headers=headers)
    assert resp.status_code == 422


# --- Autocomplete Tests ---


def test_autocomplete_empty(client):
    _, headers = _register(client)
    resp = client.get("/api/search/autocomplete", params={"q": "py"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["suggestions"] == []


def test_autocomplete_from_history(client):
    _, headers = _register(client)
    with patch("app.services.search.search_books_google", new_callable=AsyncMock) as mock_gb:
        mock_gb.return_value = ([], 0)
        client.get("/api/search", params={"q": "python programming"}, headers=headers)
        client.get("/api/search", params={"q": "python flask"}, headers=headers)

    resp = client.get("/api/search/autocomplete", params={"q": "python"}, headers=headers)
    assert resp.status_code == 200
    suggestions = resp.json()["suggestions"]
    assert len(suggestions) >= 1
    assert all("python" in s.lower() for s in suggestions)


# --- Trending Tests ---


def test_trending_empty(client):
    _, headers = _register(client)
    resp = client.get("/api/search/trending", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["searches"] == []


def test_trending_populated(client):
    h1, h2 = _register_two(client)
    with patch("app.services.search.search_books_google", new_callable=AsyncMock) as mock_gb:
        mock_gb.return_value = ([], 0)
        # Multiple users search for same term
        client.get("/api/search", params={"q": "harry potter"}, headers=h1)
        client.get("/api/search", params={"q": "harry potter"}, headers=h2)
        client.get("/api/search", params={"q": "lord of rings"}, headers=h1)

    resp = client.get("/api/search/trending", headers=h1)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["searches"]) >= 1
    # harry potter should be first (2 searches)
    assert data["searches"][0]["query"] == "harry potter"
    assert data["searches"][0]["count"] == 2


# --- Search Type Validation ---


def test_invalid_search_type(client):
    _, headers = _register(client)
    resp = client.get("/api/search", params={"q": "test", "search_type": "invalid"}, headers=headers)
    assert resp.status_code == 422
