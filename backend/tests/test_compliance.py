"""Tests for compliance features: account deletion, privacy consent, data export, legal pages."""

from tests.conftest import VALID_TEST_PASSWORD


def test_delete_account_anonymizes_data(client, db_session):
    """Account deletion should anonymize PII and deactivate user."""
    # Register a user
    resp = client.post("/api/auth/register", json={
        "email": "deleteme@example.com",
        "password": VALID_TEST_PASSWORD,
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Delete account
    resp = client.delete("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert "anonymized" in resp.json()["message"].lower()

    # Verify user is anonymized in DB
    from app.models import User
    user = db_session.query(User).filter(User.email.like("deleted_%@anonymized.local")).first()
    assert user is not None
    assert user.is_active is False
    assert user.deleted_at is not None
    assert user.hashed_password == ""
    assert user.auth_provider == "deleted"


def test_delete_account_cancels_subscription(client, db_session):
    """Account deletion should cancel active subscriptions."""
    from app.models import User
    from app.services.auth import create_access_token, hash_password

    user = User(
        email="premium@example.com",
        hashed_password=hash_password(VALID_TEST_PASSWORD),
        subscription_status="active",
        subscription_plan="premium",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete("/api/auth/me", headers=headers)
    assert resp.status_code == 200

    db_session.refresh(user)
    assert user.subscription_status == "cancelled"


def test_delete_account_unauthenticated(client):
    """Deleting account without auth should return 401."""
    resp = client.delete("/api/auth/me")
    assert resp.status_code in (401, 403)


def test_privacy_consent_get_default(client, registered_user):
    """Default consent should be false."""
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    resp = client.get("/api/auth/privacy-consent", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["analytics_consent"] is False
    assert data["marketing_consent"] is False


def test_privacy_consent_update(client, registered_user):
    """Should be able to update consent preferences."""
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}

    resp = client.put("/api/auth/privacy-consent", headers=headers, json={
        "analytics_consent": True,
        "marketing_consent": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["analytics_consent"] is True
    assert data["marketing_consent"] is False
    assert data["consent_date"] is not None

    # Verify it persists
    resp = client.get("/api/auth/privacy-consent", headers=headers)
    assert resp.json()["analytics_consent"] is True


def test_privacy_consent_update_idempotent(client, registered_user):
    """Updating consent multiple times should work."""
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}

    client.put("/api/auth/privacy-consent", headers=headers, json={
        "analytics_consent": True,
        "marketing_consent": True,
    })
    resp = client.put("/api/auth/privacy-consent", headers=headers, json={
        "analytics_consent": False,
        "marketing_consent": True,
    })
    assert resp.status_code == 200
    assert resp.json()["analytics_consent"] is False
    assert resp.json()["marketing_consent"] is True


def test_export_data(client, registered_user):
    """Data export should return user profile and data."""
    headers = {"Authorization": f"Bearer {registered_user['access_token']}"}
    resp = client.get("/api/auth/export-data", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "profile" in data
    assert "liked_books" in data
    assert "swipe_events" in data
    assert "book_lists" in data
    assert "reviews" in data
    assert "activity" in data
    assert "privacy_consent" in data
    assert data["profile"]["email"] == "test@example.com"


def test_export_data_unauthenticated(client):
    """Data export without auth should return 401."""
    resp = client.get("/api/auth/export-data")
    assert resp.status_code in (401, 403)


def test_privacy_policy_page(client):
    """Privacy policy endpoint should return HTML."""
    resp = client.get("/legal/privacy-policy")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Privacy Policy" in resp.text


def test_terms_page(client):
    """Terms endpoint should return HTML."""
    resp = client.get("/legal/terms")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "Terms of Service" in resp.text
