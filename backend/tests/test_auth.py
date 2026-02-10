def test_register_success(client):
    resp = client.post("/api/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client, registered_user):
    resp = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"]


def test_register_short_password(client):
    resp = client.post("/api/auth/register", json={
        "email": "short@example.com",
        "password": "short",
    })
    assert resp.status_code == 422


def test_register_invalid_email(client):
    resp = client.post("/api/auth/register", json={
        "email": "not-an-email",
        "password": "password123",
    })
    assert resp.status_code == 422


def test_login_success(client, registered_user):
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client, registered_user):
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


def test_login_nonexistent_user(client):
    resp = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert resp.status_code == 401


def test_refresh_token(client, registered_user):
    resp = client.post("/api/auth/refresh", json={
        "refresh_token": registered_user["refresh_token"],
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_with_access_token_fails(client, registered_user):
    resp = client.post("/api/auth/refresh", json={
        "refresh_token": registered_user["access_token"],
    })
    assert resp.status_code == 401


def test_refresh_invalid_token(client):
    resp = client.post("/api/auth/refresh", json={
        "refresh_token": "invalid.token.here",
    })
    assert resp.status_code == 401


def test_get_me(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data


def test_get_me_unauthenticated(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_get_me_invalid_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer bad.token"})
    assert resp.status_code == 401


def test_delete_account(client, auth_headers):
    resp = client.delete("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"].lower()

    # Verify user can no longer access /me
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 401
