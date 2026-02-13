"""Tests for social features: profiles, follows, book lists, activity feed, user search."""

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


# --- Profile Tests ---


def test_get_own_profile(client):
    _, headers = _register(client)
    resp = client.get("/api/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] > 0
    assert data["username"] == "user1"
    assert data["bio"] == ""
    assert data["is_public"] is True
    assert data["followers_count"] == 0
    assert data["following_count"] == 0


def test_update_profile(client):
    _, headers = _register(client)
    resp = client.put("/api/profile", headers=headers, json={
        "bio": "I love reading!",
        "reading_goal": 50,
        "is_public": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["bio"] == "I love reading!"
    assert data["reading_goal"] == 50
    assert data["is_public"] is False


def test_get_other_user_profile(client):
    h1, h2 = _register_two(client)
    # Get alice's ID
    me = client.get("/api/profile", headers=h1).json()
    alice_id = me["user_id"]
    # Bob views Alice
    resp = client.get(f"/api/profile/{alice_id}", headers=h2)
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_private_profile_forbidden(client):
    h1, h2 = _register_two(client)
    me = client.get("/api/profile", headers=h1).json()
    alice_id = me["user_id"]
    # Make Alice's profile private
    client.put("/api/profile", headers=h1, json={"is_public": False})
    # Bob tries to view
    resp = client.get(f"/api/profile/{alice_id}", headers=h2)
    assert resp.status_code == 403


# --- Follow Tests ---


def test_follow_unfollow(client):
    h1, h2 = _register_two(client)
    alice = client.get("/api/profile", headers=h1).json()
    alice_id = alice["user_id"]
    # Bob follows Alice
    resp = client.post(f"/api/social/follow/{alice_id}", headers=h2)
    assert resp.status_code == 201
    # Alice has 1 follower
    profile = client.get(f"/api/profile/{alice_id}", headers=h2).json()
    assert profile["followers_count"] == 1
    assert profile["is_following"] is True
    # Bob unfollows Alice
    resp = client.delete(f"/api/social/follow/{alice_id}", headers=h2)
    assert resp.status_code == 200
    # Alice has 0 followers
    profile = client.get(f"/api/profile/{alice_id}", headers=h2).json()
    assert profile["followers_count"] == 0
    assert profile["is_following"] is False


def test_cannot_follow_self(client):
    _, headers = _register(client)
    me = client.get("/api/profile", headers=headers).json()
    resp = client.post(f"/api/social/follow/{me['user_id']}", headers=headers)
    assert resp.status_code == 409


def test_cannot_follow_twice(client):
    h1, h2 = _register_two(client)
    alice = client.get("/api/profile", headers=h1).json()
    client.post(f"/api/social/follow/{alice['user_id']}", headers=h2)
    resp = client.post(f"/api/social/follow/{alice['user_id']}", headers=h2)
    assert resp.status_code == 409


def test_get_followers_following(client):
    h1, h2 = _register_two(client)
    alice = client.get("/api/profile", headers=h1).json()
    alice_id = alice["user_id"]
    # Bob follows Alice
    client.post(f"/api/social/follow/{alice_id}", headers=h2)
    # Alice's followers
    resp = client.get("/api/social/followers", headers=h1)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["users"][0]["username"] == "bob"
    # Bob's following
    resp = client.get("/api/social/following", headers=h2)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["users"][0]["username"] == "alice"


# --- Activity Feed Tests ---


def test_activity_feed(client):
    h1, h2 = _register_two(client)
    alice = client.get("/api/profile", headers=h1).json()
    alice_id = alice["user_id"]
    # Bob follows Alice (generates activity)
    client.post(f"/api/social/follow/{alice_id}", headers=h2)
    # Bob's feed should have the follow event
    resp = client.get("/api/social/feed", headers=h2)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    events = data["events"]
    assert any(e["event_type"] == "followed_user" for e in events)


# --- Book Lists Tests ---


def test_create_and_list_book_lists(client):
    _, headers = _register(client)
    resp = client.post("/api/book-lists", headers=headers, json={
        "name": "Summer Reading",
        "description": "Books for the beach",
        "is_public": True,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Summer Reading"
    assert data["item_count"] == 0
    # List all
    resp = client.get("/api/book-lists", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_book_list_crud(client):
    _, headers = _register(client)
    # Create
    resp = client.post("/api/book-lists", headers=headers, json={"name": "My List"})
    list_id = resp.json()["id"]
    # Update
    resp = client.put(f"/api/book-lists/{list_id}", headers=headers, json={
        "name": "Updated List",
        "description": "Updated description",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated List"
    # Get detail
    resp = client.get(f"/api/book-lists/{list_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated List"
    # Delete
    resp = client.delete(f"/api/book-lists/{list_id}", headers=headers)
    assert resp.status_code == 200


def test_add_remove_book_from_list(client):
    _, headers = _register(client)
    # Create list
    resp = client.post("/api/book-lists", headers=headers, json={"name": "Test"})
    list_id = resp.json()["id"]
    # Add book
    resp = client.post(f"/api/book-lists/{list_id}/books", headers=headers, json={
        "book_id": "abc123",
        "note": "Great book!",
    })
    assert resp.status_code == 201
    assert resp.json()["book_id"] == "abc123"
    # Verify it's in the list
    resp = client.get(f"/api/book-lists/{list_id}", headers=headers)
    assert len(resp.json()["items"]) == 1
    # Can't add same book twice
    resp = client.post(f"/api/book-lists/{list_id}/books", headers=headers, json={
        "book_id": "abc123",
    })
    assert resp.status_code == 409
    # Remove book
    resp = client.delete(f"/api/book-lists/{list_id}/books/abc123", headers=headers)
    assert resp.status_code == 200
    # Verify it's gone
    resp = client.get(f"/api/book-lists/{list_id}", headers=headers)
    assert len(resp.json()["items"]) == 0


def test_cannot_modify_other_users_list(client):
    h1, h2 = _register_two(client)
    # Alice creates a list
    resp = client.post("/api/book-lists", headers=h1, json={"name": "Alice's List"})
    list_id = resp.json()["id"]
    # Bob tries to update it
    resp = client.put(f"/api/book-lists/{list_id}", headers=h2, json={"name": "Bob's List"})
    assert resp.status_code == 403
    # Bob tries to delete it
    resp = client.delete(f"/api/book-lists/{list_id}", headers=h2)
    assert resp.status_code == 403
    # Bob tries to add a book
    resp = client.post(f"/api/book-lists/{list_id}/books", headers=h2, json={"book_id": "x"})
    assert resp.status_code == 403


def test_can_view_public_list(client):
    h1, h2 = _register_two(client)
    # Alice creates a public list
    resp = client.post("/api/book-lists", headers=h1, json={"name": "Public List"})
    list_id = resp.json()["id"]
    # Bob can view it
    resp = client.get(f"/api/book-lists/{list_id}", headers=h2)
    assert resp.status_code == 200


def test_cannot_view_private_list(client):
    h1, h2 = _register_two(client)
    # Alice creates a private list
    resp = client.post("/api/book-lists", headers=h1, json={
        "name": "Private List",
        "is_public": False,
    })
    list_id = resp.json()["id"]
    # Bob cannot view it
    resp = client.get(f"/api/book-lists/{list_id}", headers=h2)
    assert resp.status_code == 403


# --- User Search ---


def test_search_users(client):
    h1, h2 = _register_two(client)
    resp = client.get("/api/social/search?q=alice", headers=h2)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    # Bob should find Alice
    usernames = [u["username"] for u in data["users"]]
    assert "alice" in usernames


def test_search_no_results(client):
    _, headers = _register(client)
    resp = client.get("/api/social/search?q=nonexistent", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["users"]) == 0


# --- Activity from list creation ---


def test_list_creation_creates_activity(client):
    _, headers = _register(client)
    client.post("/api/book-lists", headers=headers, json={"name": "Activity Test"})
    resp = client.get("/api/social/feed", headers=headers)
    events = resp.json()["events"]
    assert any(e["event_type"] == "created_list" for e in events)
