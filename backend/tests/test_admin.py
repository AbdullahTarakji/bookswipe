"""Tests for admin endpoints."""

from tests.conftest import VALID_TEST_PASSWORD


def test_list_users_requires_admin(client, auth_headers):
    """Regular users cannot access admin endpoints."""
    resp = client.get("/api/admin/users", headers=auth_headers)
    assert resp.status_code == 401
    assert "admin" in resp.json()["detail"].lower()


def test_list_users_no_auth(client):
    """Unauthenticated requests get 401."""
    resp = client.get("/api/admin/users")
    assert resp.status_code == 401


def test_list_users_success(client, admin_headers, regular_user):
    """Admin can list all users."""
    resp = client.get("/api/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert "total" in data
    assert data["total"] >= 2  # admin + regular user
    assert data["page"] == 1


def test_list_users_pagination(client, admin_headers, db_session):
    """Admin can paginate user list."""
    from app.models import User
    from app.services.auth import hash_password

    for i in range(5):
        db_session.add(User(
            email=f"page_user_{i}@test.com",
            hashed_password=hash_password(VALID_TEST_PASSWORD),
        ))
    db_session.commit()

    resp = client.get("/api/admin/users?page=1&page_size=3", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["users"]) == 3
    assert data["page_size"] == 3


def test_list_users_search(client, admin_headers, regular_user):
    """Admin can search users by email."""
    resp = client.get("/api/admin/users?search=regular", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any("regular" in u["email"] for u in data["users"])


def test_list_users_filter_role(client, admin_headers, regular_user):
    """Admin can filter by role."""
    resp = client.get("/api/admin/users?role=admin", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert all(u["role"] == "admin" for u in data["users"])


def test_list_users_filter_banned(client, admin_headers, regular_user):
    """Admin can filter by ban status."""
    resp = client.get("/api/admin/users?is_banned=false", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert all(u["is_banned"] is False for u in data["users"])


def test_get_user_detail(client, admin_headers, regular_user):
    """Admin can get user details."""
    resp = client.get(f"/api/admin/users/{regular_user.id}", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == regular_user.id
    assert data["email"] == "regular@test.com"
    assert data["role"] == "user"


def test_get_user_not_found(client, admin_headers):
    """Requesting a nonexistent user returns 404."""
    resp = client.get("/api/admin/users/99999", headers=admin_headers)
    assert resp.status_code == 404


def test_update_role(client, admin_headers, regular_user):
    """Admin can change a user's role."""
    resp = client.put(
        f"/api/admin/users/{regular_user.id}/role",
        json={"role": "admin"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_update_role_invalid(client, admin_headers, regular_user):
    """Invalid role value is rejected."""
    resp = client.put(
        f"/api/admin/users/{regular_user.id}/role",
        json={"role": "superadmin"},
        headers=admin_headers,
    )
    assert resp.status_code == 422


def test_update_own_role(client, admin_headers, admin_user):
    """Admin cannot change their own role."""
    resp = client.put(
        f"/api/admin/users/{admin_user.id}/role",
        json={"role": "user"},
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_ban_user(client, admin_headers, regular_user):
    """Admin can ban a user."""
    resp = client.put(
        f"/api/admin/users/{regular_user.id}/ban",
        json={"reason": "Spam"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_banned"] is True
    assert data["ban_reason"] == "Spam"
    assert data["banned_at"] is not None


def test_unban_user(client, admin_headers, regular_user):
    """Banning an already banned user unbans them (toggle)."""
    # First ban
    client.put(
        f"/api/admin/users/{regular_user.id}/ban",
        json={"reason": "Spam"},
        headers=admin_headers,
    )
    # Then unban (toggle)
    resp = client.put(
        f"/api/admin/users/{regular_user.id}/ban",
        json={},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_banned"] is False
    assert resp.json()["ban_reason"] is None


def test_ban_self(client, admin_headers, admin_user):
    """Admin cannot ban themselves."""
    resp = client.put(
        f"/api/admin/users/{admin_user.id}/ban",
        json={},
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_ban_admin(client, admin_headers, db_session):
    """Cannot ban another admin user."""
    from app.models import User
    from app.services.auth import hash_password

    other_admin = User(
        email="other_admin@test.com",
        hashed_password=hash_password(VALID_TEST_PASSWORD),
        role="admin",
    )
    db_session.add(other_admin)
    db_session.commit()
    db_session.refresh(other_admin)

    resp = client.put(
        f"/api/admin/users/{other_admin.id}/ban",
        json={},
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_delete_user(client, admin_headers, regular_user):
    """Admin can hard-delete a user."""
    resp = client.delete(
        f"/api/admin/users/{regular_user.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"].lower()

    # Verify user is gone
    resp = client.get(f"/api/admin/users/{regular_user.id}", headers=admin_headers)
    assert resp.status_code == 404


def test_delete_self(client, admin_headers, admin_user):
    """Admin cannot delete themselves."""
    resp = client.delete(
        f"/api/admin/users/{admin_user.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_delete_admin(client, admin_headers, db_session):
    """Cannot delete another admin user."""
    from app.models import User
    from app.services.auth import hash_password

    other_admin = User(
        email="other_admin2@test.com",
        hashed_password=hash_password(VALID_TEST_PASSWORD),
        role="admin",
    )
    db_session.add(other_admin)
    db_session.commit()
    db_session.refresh(other_admin)

    resp = client.delete(
        f"/api/admin/users/{other_admin.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_analytics(client, admin_headers, regular_user):
    """Admin can access analytics endpoint."""
    resp = client.get("/api/admin/analytics", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "active_users_7d" in data
    assert "banned_users" in data
    assert "admin_users" in data
    assert "total_likes" in data
    assert "total_skips" in data
    assert "user_growth" in data
    assert "popular_categories" in data
    assert "recent_users" in data
    assert data["total_users"] >= 2


def test_analytics_requires_admin(client, auth_headers):
    """Regular users cannot access analytics."""
    resp = client.get("/api/admin/analytics", headers=auth_headers)
    assert resp.status_code == 401


def test_system_info(client, admin_headers):
    """Admin can access system info endpoint."""
    resp = client.get("/api/admin/system", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "app_version" in data
    assert "python_version" in data
    assert "uptime_seconds" in data
    assert "uptime_human" in data
    assert "database" in data
    assert "memory_usage_mb" in data
    assert "pid" in data
    assert "platform" in data
    assert "environment" in data


def test_system_info_requires_admin(client, auth_headers):
    """Regular users cannot access system info."""
    resp = client.get("/api/admin/system", headers=auth_headers)
    assert resp.status_code == 401


def test_get_me_includes_role(client, auth_headers):
    """GET /api/auth/me returns the user's role."""
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "role" in data
    assert data["role"] == "user"
