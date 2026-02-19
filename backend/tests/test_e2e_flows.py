"""End-to-end integration tests exercising full user flows across multiple endpoints.

These tests simulate realistic user journeys through the BookSwipe API:
- Registration → Login → Discover → Swipe → Favorites → Logout
- Token lifecycle including refresh and revocation
- Error handling for invalid tokens and duplicate actions
"""

from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import VALID_TEST_PASSWORD


class TestAuthFlowE2E:
    """Full authentication lifecycle: register → login → refresh → access → logout → revoked."""

    def test_full_auth_lifecycle(self, client):
        """Register, login, use token, refresh, logout, and verify revocation."""
        # 1. Register
        reg = client.post("/api/auth/register", json={
            "email": "e2e_auth@example.com",
            "password": VALID_TEST_PASSWORD,
        })
        assert reg.status_code == 201
        reg_data = reg.json()
        access_token = reg_data["access_token"]
        refresh_token = reg_data["refresh_token"]

        # 2. Access protected endpoint
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me.status_code == 200
        assert me.json()["email"] == "e2e_auth@example.com"

        # 3. Login with same credentials
        login = client.post("/api/auth/login", json={
            "email": "e2e_auth@example.com",
            "password": VALID_TEST_PASSWORD,
        })
        assert login.status_code == 200
        login_token = login.json()["access_token"]

        # 4. Both tokens should work
        me2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login_token}"})
        assert me2.status_code == 200

        # 5. Refresh the registration token
        refreshed = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert refreshed.status_code == 200
        new_access = refreshed.json()["access_token"]
        new_refresh = refreshed.json()["refresh_token"]
        assert new_access != access_token

        # 6. Old refresh token should be revoked (token rotation)
        stale = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert stale.status_code == 401

        # 7. New tokens work
        me3 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_access}"})
        assert me3.status_code == 200

        # 8. Logout revokes the current access token
        logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {new_access}"})
        assert logout.status_code == 200

        # 9. Revoked token should fail
        me4 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {new_access}"})
        assert me4.status_code == 401

        # 10. Can still refresh with the new refresh token and access the API
        refreshed2 = client.post("/api/auth/refresh", json={"refresh_token": new_refresh})
        assert refreshed2.status_code == 200
        final_token = refreshed2.json()["access_token"]
        me5 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {final_token}"})
        assert me5.status_code == 200

    def test_register_login_delete_reregister(self, client):
        """Register, soft-delete account, then verify re-registration succeeds."""
        # Register
        reg = client.post("/api/auth/register", json={
            "email": "delete_me@example.com",
            "password": VALID_TEST_PASSWORD,
        })
        assert reg.status_code == 201
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        # Delete account
        delete = client.delete("/api/auth/me", headers=headers)
        assert delete.status_code == 200

        # Token is now invalid
        me = client.get("/api/auth/me", headers=headers)
        assert me.status_code == 401

        # Login fails for soft-deleted user
        login = client.post("/api/auth/login", json={
            "email": "delete_me@example.com",
            "password": VALID_TEST_PASSWORD,
        })
        assert login.status_code == 401

        # Re-registration with same email succeeds (soft-deleted/anonymized account)
        re_reg = client.post("/api/auth/register", json={
            "email": "delete_me@example.com",
            "password": VALID_TEST_PASSWORD,
        })
        assert re_reg.status_code == 201


class TestBookDiscoveryFlowE2E:
    """Full book discovery flow: browse → like → skip → favorites → unlike."""

    def test_browse_like_skip_favorites_unlike(self, client, auth_headers, mock_google_books_search):
        """Simulate a complete discovery session with swipe actions."""
        # 1. Browse books
        discover = client.get("/api/books/discover?category=fiction", headers=auth_headers)
        assert discover.status_code == 200
        books = discover.json()["books"]
        assert len(books) >= 2

        # 2. Like the first book
        like = client.post("/api/books/like", json={
            "google_book_id": books[0]["google_book_id"],
            "title": books[0]["title"],
            "authors": ", ".join(books[0]["authors"]),
            "thumbnail": books[0].get("thumbnail", ""),
        }, headers=auth_headers)
        assert like.status_code == 201

        # 3. Skip the second book
        skip = client.post("/api/books/skip", json={
            "google_book_id": books[1]["google_book_id"],
        }, headers=auth_headers)
        assert skip.status_code == 201

        # 4. Favorites should show the liked book
        liked = client.get("/api/books/liked", headers=auth_headers)
        assert liked.status_code == 200
        liked_ids = [b["google_book_id"] for b in liked.json()["books"]]
        assert books[0]["google_book_id"] in liked_ids

        # 5. Re-browsing should exclude both liked and skipped books
        discover2 = client.get("/api/books/discover?category=fiction", headers=auth_headers)
        assert discover2.status_code == 200
        remaining_ids = [b["google_book_id"] for b in discover2.json()["books"]]
        assert books[0]["google_book_id"] not in remaining_ids
        assert books[1]["google_book_id"] not in remaining_ids

        # 6. Unlike the book
        unlike = client.delete(
            f"/api/books/liked/{books[0]['google_book_id']}",
            headers=auth_headers,
        )
        assert unlike.status_code == 200

        # 7. Favorites should be empty
        liked2 = client.get("/api/books/liked", headers=auth_headers)
        assert liked2.status_code == 200
        assert liked2.json()["total"] == 0

    def test_guest_can_browse_but_not_like(self, client, mock_google_books_search):
        """Unauthenticated users can discover books but cannot like or skip."""
        discover = client.get("/api/books/discover?category=fiction")
        assert discover.status_code == 200
        assert len(discover.json()["books"]) > 0

        like = client.post("/api/books/like", json={
            "google_book_id": "book_1",
            "title": "Test",
            "authors": "Author",
            "thumbnail": "",
        })
        assert like.status_code == 401

        skip = client.post("/api/books/skip", json={"google_book_id": "book_1"})
        assert skip.status_code == 401


class TestBookDetailE2E:
    """Book detail and cover proxy endpoint tests."""

    def test_get_book_detail_returns_full_info(self, client, mock_google_book_detail):
        """Book detail endpoint returns all metadata fields."""
        resp = client.get("/api/books/book_1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["google_book_id"] == "book_1"
        assert data["title"] == "Test Book One"
        assert data["authors"] == ["Author A"]
        assert data["description"] == "A test book description."
        assert data["page_count"] == 200
        assert data["average_rating"] == 4.0
        assert data["ratings_count"] == 100
        assert data["published_date"] == "2023-01-01"
        assert data["publisher"] == "Test Publisher"

    def test_cover_proxy_returns_image(self, client):
        """Cover proxy fetches and returns an image from Google Books."""
        fake_image = b"\x89PNG" + b"\x00" * 6000  # >5000 bytes

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_image
        mock_response.headers = {"content-type": "image/png"}

        with patch("app.routers.books.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            resp = client.get("/api/books/cover-proxy/test_book_id")
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "image/png"
            assert resp.headers["cache-control"] == "public, max-age=86400"

    def test_cover_proxy_not_found(self, client):
        """Cover proxy returns 404 when no image is available."""
        # All image responses are small (below 5000 bytes threshold)
        small_image = b"\x89PNG" + b"\x00" * 100

        mock_img_response = MagicMock()
        mock_img_response.status_code = 200
        mock_img_response.content = small_image
        mock_img_response.headers = {"content-type": "image/png"}

        # Volume API returns no imageLinks
        mock_vol_response = MagicMock()
        mock_vol_response.status_code = 200
        mock_vol_response.json.return_value = {"volumeInfo": {}}

        responses = [mock_img_response] * 4 + [mock_vol_response]

        with patch("app.routers.books.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = responses
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            resp = client.get("/api/books/cover-proxy/no_image_book")
            assert resp.status_code == 404


class TestTokenEdgeCases:
    """Edge cases for token validation and error handling."""

    def test_expired_access_token_format(self, client):
        """A completely malformed token returns 401."""
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
        assert resp.status_code == 401

    def test_empty_bearer_token(self, client):
        """An empty bearer header returns 401."""
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer "})
        assert resp.status_code == 401

    def test_no_auth_header(self, client):
        """Missing Authorization header returns 401."""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_wrong_auth_scheme(self, client):
        """Using Basic auth scheme instead of Bearer returns 401."""
        resp = client.get("/api/auth/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert resp.status_code == 401

    def test_refresh_with_empty_body(self, client):
        """Refresh endpoint with missing body returns 422."""
        resp = client.post("/api/auth/refresh", json={})
        assert resp.status_code == 422

    def test_register_empty_body(self, client):
        """Register endpoint with empty body returns 422."""
        resp = client.post("/api/auth/register", json={})
        assert resp.status_code == 422

    def test_login_empty_body(self, client):
        """Login endpoint with empty body returns 422."""
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 422


class TestCategoriesE2E:
    """Categories flow: list → detail → use for discovery."""

    def test_list_and_use_category(self, client, mock_google_books_search):
        """Fetch categories, then use one for book discovery."""
        # List categories
        cats = client.get("/api/categories")
        assert cats.status_code == 200
        categories = cats.json()
        assert len(categories) > 0

        # Use a category for discovery
        cat_key = categories[0]["google_category_key"]
        discover = client.get(f"/api/books/discover?category={cat_key}")
        assert discover.status_code == 200
        assert "books" in discover.json()


class TestAdminFlowE2E:
    """Admin workflow: list users → inspect → modify → verify."""

    def test_admin_user_management_flow(self, client, admin_headers, regular_user):
        """Admin lists users, bans one, verifies, then unbans."""
        # 1. List users
        users = client.get("/api/admin/users", headers=admin_headers)
        assert users.status_code == 200
        assert users.json()["total"] >= 2

        # 2. Get the regular user's detail
        detail = client.get(f"/api/admin/users/{regular_user.id}", headers=admin_headers)
        assert detail.status_code == 200
        assert detail.json()["is_banned"] is False

        # 3. Ban the user
        ban = client.put(
            f"/api/admin/users/{regular_user.id}/ban",
            json={"reason": "E2E test ban"},
            headers=admin_headers,
        )
        assert ban.status_code == 200
        assert ban.json()["is_banned"] is True
        assert ban.json()["ban_reason"] == "E2E test ban"

        # 4. Verify in list with banned filter
        banned = client.get("/api/admin/users?is_banned=true", headers=admin_headers)
        assert banned.status_code == 200
        banned_ids = [u["id"] for u in banned.json()["users"]]
        assert regular_user.id in banned_ids

        # 5. Unban (toggle)
        unban = client.put(
            f"/api/admin/users/{regular_user.id}/ban",
            json={},
            headers=admin_headers,
        )
        assert unban.status_code == 200
        assert unban.json()["is_banned"] is False

    def test_admin_analytics_and_system(self, client, admin_headers, regular_user):
        """Admin can view analytics and system info."""
        analytics = client.get("/api/admin/analytics", headers=admin_headers)
        assert analytics.status_code == 200
        data = analytics.json()
        assert data["total_users"] >= 2
        assert "user_growth" in data
        assert "popular_categories" in data

        system = client.get("/api/admin/system", headers=admin_headers)
        assert system.status_code == 200
        sys_data = system.json()
        assert "app_version" in sys_data
        assert "python_version" in sys_data
        assert "uptime_seconds" in sys_data


class TestSwipeLimitFlowE2E:
    """Swipe limit enforcement across the full discovery flow."""

    def test_swipe_status_updates_after_actions(self, client, mock_google_books_search):
        """Swipe counter increments and status endpoint reflects it."""
        # Register a fresh user for this test
        reg = client.post("/api/auth/register", json={
            "email": "swipe_e2e@example.com",
            "password": VALID_TEST_PASSWORD,
        })
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        # Check initial status
        status = client.get("/api/payments/swipe-status", headers=headers)
        assert status.status_code == 200
        assert status.json()["swipes_today"] == 0
        assert status.json()["swipes_remaining"] == 10

        # Like a book
        client.post("/api/books/like", json={
            "google_book_id": "swipe_e2e_book_1",
            "title": "Swipe Test",
            "authors": "Author",
            "thumbnail": "",
        }, headers=headers)

        # Skip another
        client.post("/api/books/skip", json={
            "google_book_id": "swipe_e2e_book_2",
        }, headers=headers)

        # Status should show 2 swipes used
        status2 = client.get("/api/payments/swipe-status", headers=headers)
        assert status2.status_code == 200
        assert status2.json()["swipes_today"] == 2
        assert status2.json()["swipes_remaining"] == 8


class TestCrossEndpointConsistency:
    """Tests ensuring data consistency across related endpoints."""

    def test_user_profile_matches_registration(self, client):
        """Profile endpoint returns the same email used during registration."""
        reg = client.post("/api/auth/register", json={
            "email": "consistency@example.com",
            "password": VALID_TEST_PASSWORD,
        })
        headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

        me = client.get("/api/auth/me", headers=headers)
        assert me.json()["email"] == "consistency@example.com"
        assert me.json()["role"] == "user"
        assert me.json()["subscription_status"] == "free"

    def test_liked_book_appears_in_list(self, client, auth_headers):
        """A book liked via POST appears in the GET liked list."""
        client.post("/api/books/like", json={
            "google_book_id": "consistency_book",
            "title": "Consistency Check",
            "authors": "Test Author",
            "thumbnail": "http://example.com/thumb.jpg",
        }, headers=auth_headers)

        liked = client.get("/api/books/liked", headers=auth_headers)
        books = liked.json()["books"]
        assert any(b["google_book_id"] == "consistency_book" for b in books)
        match = next(b for b in books if b["google_book_id"] == "consistency_book")
        assert match["title"] == "Consistency Check"
