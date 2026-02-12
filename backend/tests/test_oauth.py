from unittest.mock import patch

from tests.conftest import VALID_TEST_PASSWORD


# --- Google OAuth Tests ---


def test_google_auth_creates_new_user(client):
    """Google sign-in with a new email creates a user and returns tokens."""
    with patch("app.routers.auth.verify_google_token") as mock_verify:
        mock_verify.return_value = {"sub": "google-uid-123", "email": "googleuser@example.com"}
        resp = client.post("/api/auth/google", json={"id_token": "fake-google-token"})

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_google_auth_links_existing_email_user(client, registered_user):
    """Google sign-in with an existing email links to that account."""
    with patch("app.routers.auth.verify_google_token") as mock_verify:
        mock_verify.return_value = {"sub": "google-uid-456", "email": "test@example.com"}
        resp = client.post("/api/auth/google", json={"id_token": "fake-google-token"})

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    # Verify it's the same user account - use the new token to get /me
    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "test@example.com"


def test_google_auth_returning_user(client):
    """Google sign-in for a returning Google user works."""
    with patch("app.routers.auth.verify_google_token") as mock_verify:
        mock_verify.return_value = {"sub": "google-uid-789", "email": "returning@example.com"}
        # First login - creates user
        resp1 = client.post("/api/auth/google", json={"id_token": "token1"})
        assert resp1.status_code == 200

        # Second login - returns same user
        resp2 = client.post("/api/auth/google", json={"id_token": "token2"})
        assert resp2.status_code == 200

    # Both should work and return tokens
    me1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {resp2.json()['access_token']}"})
    assert me1.json()["email"] == "returning@example.com"


def test_google_auth_invalid_token(client):
    """Google sign-in with an invalid token returns 401."""
    with patch("app.routers.auth.verify_google_token") as mock_verify:
        mock_verify.side_effect = ValueError("Invalid Google token: bad token")
        resp = client.post("/api/auth/google", json={"id_token": "bad-token"})

    assert resp.status_code == 401
    assert "Invalid Google token" in resp.json()["detail"]


def test_google_auth_missing_id_token(client):
    """Google sign-in without id_token returns 422."""
    resp = client.post("/api/auth/google", json={})
    assert resp.status_code == 422


# --- Apple OAuth Tests ---


def test_apple_auth_creates_new_user(client):
    """Apple sign-in with a new email creates a user and returns tokens."""
    with patch("app.routers.auth.verify_apple_token") as mock_verify:
        mock_verify.return_value = {"sub": "apple-uid-123", "email": "appleuser@example.com"}
        resp = client.post("/api/auth/apple", json={
            "authorization_code": "fake-auth-code",
            "identity_token": "fake-apple-token",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_apple_auth_links_existing_email_user(client, registered_user):
    """Apple sign-in with an existing email links to that account."""
    with patch("app.routers.auth.verify_apple_token") as mock_verify:
        mock_verify.return_value = {"sub": "apple-uid-456", "email": "test@example.com"}
        resp = client.post("/api/auth/apple", json={
            "authorization_code": "fake-auth-code",
            "identity_token": "fake-apple-token",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "test@example.com"


def test_apple_auth_returning_user(client):
    """Apple sign-in for a returning Apple user works."""
    with patch("app.routers.auth.verify_apple_token") as mock_verify:
        mock_verify.return_value = {"sub": "apple-uid-789", "email": "apple-return@example.com"}
        resp1 = client.post("/api/auth/apple", json={
            "authorization_code": "code1",
            "identity_token": "token1",
        })
        assert resp1.status_code == 200

        resp2 = client.post("/api/auth/apple", json={
            "authorization_code": "code2",
            "identity_token": "token2",
        })
        assert resp2.status_code == 200

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {resp2.json()['access_token']}"})
    assert me.json()["email"] == "apple-return@example.com"


def test_apple_auth_invalid_token(client):
    """Apple sign-in with an invalid token returns 401."""
    with patch("app.routers.auth.verify_apple_token") as mock_verify:
        mock_verify.side_effect = ValueError("Invalid Apple token: bad token")
        resp = client.post("/api/auth/apple", json={
            "authorization_code": "bad-code",
            "identity_token": "bad-token",
        })

    assert resp.status_code == 401
    assert "Invalid Apple token" in resp.json()["detail"]


def test_apple_auth_missing_fields(client):
    """Apple sign-in without required fields returns 422."""
    resp = client.post("/api/auth/apple", json={"authorization_code": "code-only"})
    assert resp.status_code == 422


# --- Cross-Provider Account Linking ---


def test_cross_provider_linking_google_then_apple(client):
    """Same email from Google then Apple links to the same account."""
    email = "shared@example.com"

    with patch("app.routers.auth.verify_google_token") as mock_google:
        mock_google.return_value = {"sub": "google-shared-123", "email": email}
        google_resp = client.post("/api/auth/google", json={"id_token": "google-token"})
    assert google_resp.status_code == 200

    with patch("app.routers.auth.verify_apple_token") as mock_apple:
        mock_apple.return_value = {"sub": "apple-shared-456", "email": email}
        apple_resp = client.post("/api/auth/apple", json={
            "authorization_code": "apple-code",
            "identity_token": "apple-token",
        })
    assert apple_resp.status_code == 200

    # Both tokens should resolve to the same user
    me_google = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {google_resp.json()['access_token']}"
    })
    me_apple = client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {apple_resp.json()['access_token']}"
    })
    assert me_google.json()["id"] == me_apple.json()["id"]
    assert me_google.json()["email"] == email


def test_oauth_user_can_access_protected_endpoints(client):
    """OAuth-created user can access authenticated endpoints."""
    with patch("app.routers.auth.verify_google_token") as mock_verify:
        mock_verify.return_value = {"sub": "google-access-test", "email": "access@example.com"}
        resp = client.post("/api/auth/google", json={"id_token": "token"})

    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    # Should be able to access /me
    me_resp = client.get("/api/auth/me", headers=headers)
    assert me_resp.status_code == 200

    # Should be able to logout
    logout_resp = client.post("/api/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
