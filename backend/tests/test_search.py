"""Tests for search functionality: unified search, history, autocomplete, trending."""

from unittest.mock import AsyncMock, patch

from tests.conftest import VALID_TEST_PASSWORD


# --- Helpers ---


def _register(client, email="user1@example.com"):
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": VALID_TEST_PASSWORD,
    })
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    return data, headers


def _register_two(client):
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


@patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0))
def test_search_records_history(mock_google, client):
    _, headers = _register(client)
    # Perform a search
    resp = client.get("/api/search?q=python", headers=headers)
    assert resp.status_code == 200

    # Check history
    resp = client.get("/api/search/history", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["query"] == "python"
    assert data["items"][0]["search_type"] == "all"


@patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0))
def test_search_history_records_type(mock_google, client):
    _, headers = _register(client)
    client.get("/api/search?q=fantasy&search_type=books", headers=headers)

    resp = client.get("/api/search/history", headers=headers)
    data = resp.json()
    assert data["items"][0]["search_type"] == "books"


def test_clear_search_history(client):
    _, headers = _register(client)

    # Add history entries directly via autocomplete won't work, use search
    with patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0)):
        client.get("/api/search?q=test1", headers=headers)
        client.get("/api/search?q=test2", headers=headers)

    # Verify history exists
    resp = client.get("/api/search/history", headers=headers)
    assert resp.json()["total"] == 2

    # Clear
    resp = client.delete("/api/search/history", headers=headers)
    assert resp.status_code == 200
    assert "Cleared 2" in resp.json()["message"]

    # Verify empty
    resp = client.get("/api/search/history", headers=headers)
    assert resp.json()["total"] == 0


def test_delete_single_history_item(client):
    _, headers = _register(client)

    with patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0)):
        client.get("/api/search?q=delete_me", headers=headers)

    history = client.get("/api/search/history", headers=headers).json()
    item_id = history["items"][0]["id"]

    resp = client.delete(f"/api/search/history/{item_id}", headers=headers)
    assert resp.status_code == 200

    # Verify deleted
    resp = client.get("/api/search/history", headers=headers)
    assert resp.json()["total"] == 0


def test_delete_nonexistent_history_item(client):
    _, headers = _register(client)
    resp = client.delete("/api/search/history/99999", headers=headers)
    assert resp.status_code == 404


def test_history_isolated_per_user(client):
    h1, h2 = _register_two(client)

    with patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0)):
        client.get("/api/search?q=alice_query", headers=h1)
        client.get("/api/search?q=bob_query", headers=h2)

    alice_history = client.get("/api/search/history", headers=h1).json()
    bob_history = client.get("/api/search/history", headers=h2).json()

    assert alice_history["total"] == 1
    assert alice_history["items"][0]["query"] == "alice_query"
    assert bob_history["total"] == 1
    assert bob_history["items"][0]["query"] == "bob_query"


# --- Autocomplete Tests ---


def test_autocomplete_empty(client):
    _, headers = _register(client)
    resp = client.get("/api/search/autocomplete?q=xyz", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["suggestions"] == []


def test_autocomplete_returns_user_history(client):
    _, headers = _register(client)

    with patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0)):
        client.get("/api/search?q=python programming", headers=headers)
        client.get("/api/search?q=python basics", headers=headers)

    resp = client.get("/api/search/autocomplete?q=python", headers=headers)
    data = resp.json()
    assert len(data["suggestions"]) >= 1
    assert all("python" in s.lower() for s in data["suggestions"])


# --- Trending Tests ---


def test_trending_empty(client):
    _, headers = _register(client)
    resp = client.get("/api/search/trending", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["searches"] == []


def test_trending_returns_popular(client):
    h1, h2 = _register_two(client)

    with patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0)):
        # Both users search the same thing
        client.get("/api/search?q=trending_topic", headers=h1)
        client.get("/api/search?q=trending_topic", headers=h2)
        client.get("/api/search?q=unique_topic", headers=h1)

    resp = client.get("/api/search/trending", headers=h1)
    data = resp.json()
    assert len(data["searches"]) >= 1
    # trending_topic should be first (2 searches vs 1)
    assert data["searches"][0]["query"] == "trending_topic"
    assert data["searches"][0]["count"] == 2


# --- Unified Search Tests ---


@patch("app.services.search.search_books_google", new_callable=AsyncMock)
def test_unified_search_books(mock_google, client):
    from app.schemas import BookSearchResult

    mock_google.return_value = (
        [BookSearchResult(
            google_book_id="abc123",
            title="Test Book",
            authors=["Author One"],
            thumbnail="/api/books/cover-proxy/abc123?v=2",
        )],
        1,
    )

    _, headers = _register(client)
    resp = client.get("/api/search?q=test&search_type=books", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_books"] == 1
    assert data["books"][0]["title"] == "Test Book"
    assert data["users"] == []
    assert data["lists"] == []


def test_unified_search_users(client):
    h1, h2 = _register_two(client)

    with patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0)):
        resp = client.get("/api/search?q=alice&search_type=users", headers=h2)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] >= 1
    assert any(u["username"] == "alice" for u in data["users"])


def test_unified_search_lists(client):
    _, h1 = _register(client, "listowner@example.com")

    # Create a public list
    client.post("/api/book-lists", headers=h1, json={
        "name": "Best Sci-Fi Books",
        "description": "My favorite science fiction",
        "is_public": True,
    })

    _, h2 = _register(client, "searcher@example.com")

    with patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0)):
        resp = client.get("/api/search?q=sci-fi&search_type=lists", headers=h2)

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_lists"] >= 1
    assert any("Sci-Fi" in lst["name"] for lst in data["lists"])


@patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0))
def test_unified_search_all(mock_google, client):
    _, headers = _register(client)
    resp = client.get("/api/search?q=test", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    # Should have all keys
    assert "books" in data
    assert "users" in data
    assert "lists" in data


# --- Filter Tests ---


@patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0))
def test_search_with_category_filter(mock_google, client):
    _, headers = _register(client)
    resp = client.get("/api/search?q=test&category=fiction", headers=headers)
    assert resp.status_code == 200
    # Verify the filter was passed through
    call_args = mock_google.call_args
    filters = call_args[1].get("filters") or call_args[0][1]
    assert filters.category == "fiction"


@patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0))
def test_search_with_author_filter(mock_google, client):
    _, headers = _register(client)
    resp = client.get("/api/search?q=test&author=tolkien", headers=headers)
    assert resp.status_code == 200
    call_args = mock_google.call_args
    filters = call_args[1].get("filters") or call_args[0][1]
    assert filters.author == "tolkien"


@patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0))
def test_search_with_rating_filter(mock_google, client):
    _, headers = _register(client)
    resp = client.get("/api/search?q=test&min_rating=4.0", headers=headers)
    assert resp.status_code == 200
    call_args = mock_google.call_args
    filters = call_args[1].get("filters") or call_args[0][1]
    assert filters.min_rating == 4.0


@patch("app.services.search.search_books_google", new_callable=AsyncMock, return_value=([], 0))
def test_search_with_year_filters(mock_google, client):
    _, headers = _register(client)
    resp = client.get("/api/search?q=test&year_from=2020&year_to=2024", headers=headers)
    assert resp.status_code == 200
    call_args = mock_google.call_args
    filters = call_args[1].get("filters") or call_args[0][1]
    assert filters.year_from == 2020
    assert filters.year_to == 2024


# --- Validation Tests ---


def test_search_requires_query(client):
    _, headers = _register(client)
    resp = client.get("/api/search", headers=headers)
    assert resp.status_code == 422


def test_search_invalid_type(client):
    _, headers = _register(client)
    resp = client.get("/api/search?q=test&search_type=invalid", headers=headers)
    assert resp.status_code == 422


def test_search_requires_auth(client):
    resp = client.get("/api/search?q=test")
    assert resp.status_code in (401, 403)


def test_autocomplete_requires_auth(client):
    resp = client.get("/api/search/autocomplete?q=test")
    assert resp.status_code in (401, 403)


def test_history_requires_auth(client):
    resp = client.get("/api/search/history")
    assert resp.status_code in (401, 403)
