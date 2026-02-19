"""Authentication router: registration, login, OAuth, token refresh, and account management."""

import logging

from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import AuthError, ValidationError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas import (
    AppleAuthRequest,
    GoogleAuthRequest,
    MessageResponse,
    PrivacyConsentResponse,
    PrivacyConsentUpdate,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    check_password_strength,
)
from app.services.auth import (
    blacklist_token_async,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    oauth2_scheme,
    verify_password,
)
from app.metrics import auth_attempts_total
from app.services.oauth import verify_apple_token, verify_google_token

logger = logging.getLogger("bookswipe")
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _get_or_create_oauth_user(repo: UserRepository, email: str, provider: str, provider_id: str) -> User:
    """Find existing user by email or create a new one for OAuth login.

    If user exists with same email from a different provider, link accounts
    by updating provider fields (same email = same account).
    """
    user = repo.get_by_email(email)
    if user:
        # Link: update provider info if this is a different provider
        if user.auth_provider != provider:
            repo.update_provider(user, provider, provider_id)
        return user
    # Create new user (no password for OAuth users)
    return repo.create(
        email=email,
        hashed_password="",
        auth_provider=provider,
        provider_id=provider_id,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, body: UserRegister, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    repo = UserRepository(db)
    existing = repo.get_by_email(body.email, active_only=False)
    if existing:
        raise ValidationError("Email already registered")
    user = repo.create(email=body.email, hashed_password=hash_password(body.password))
    strength = check_password_strength(body.password)
    auth_attempts_total.labels(method="register", status="success").inc()

    # Send welcome email (non-blocking — failure doesn't break registration)
    try:
        from app.services.email_service import send_email
        from app.services.email_templates import render_welcome
        from app.config import settings as app_settings

        subject, html = render_welcome(user.email, app_url=app_settings.app_url)
        send_email(user.email, subject, html)
    except Exception:
        logger.warning("Failed to send welcome email to %s", body.email)

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        password_strength=strength,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, body: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user with email and password."""
    repo = UserRepository(db)
    user = repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        auth_attempts_total.labels(method="login", status="failure").inc()
        raise AuthError("Invalid email or password")
    auth_attempts_total.labels(method="login", status="success").inc()
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/google", response_model=TokenResponse)
@limiter.limit("5/minute")
def google_auth(request: Request, body: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate or register a user via Google OAuth."""
    try:
        google_user = verify_google_token(body.id_token)
    except ValueError as e:
        auth_attempts_total.labels(method="google", status="failure").inc()
        raise AuthError(str(e))
    repo = UserRepository(db)
    user = _get_or_create_oauth_user(
        repo,
        email=google_user["email"],
        provider="google",
        provider_id=google_user["sub"],
    )
    auth_attempts_total.labels(method="google", status="success").inc()
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/apple", response_model=TokenResponse)
@limiter.limit("5/minute")
def apple_auth(request: Request, body: AppleAuthRequest, db: Session = Depends(get_db)):
    """Authenticate or register a user via Apple OAuth."""
    try:
        apple_user = verify_apple_token(body.identity_token)
    except ValueError as e:
        auth_attempts_total.labels(method="apple", status="failure").inc()
        raise AuthError(str(e))
    repo = UserRepository(db)
    user = _get_or_create_oauth_user(
        repo,
        email=apple_user["email"],
        provider="apple",
        provider_id=apple_user["sub"],
    )
    auth_attempts_total.labels(method="apple", status="success").inc()
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Invalidate the current access token."""
    if token:
        await blacklist_token_async(token, db)
    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
async def refresh_token(request: Request, body: TokenRefresh, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access/refresh token pair."""
    user_id = decode_token(body.refresh_token, expected_type="refresh", db=db)
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise AuthError("User not found")
    # Rotate: blacklist old refresh token, issue new pair
    await blacklist_token_async(body.refresh_token, db)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user


@router.delete("/me", response_model=MessageResponse)
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete the authenticated user's account: anonymize PII, cancel subscriptions (GDPR/App Store compliance)."""
    original_email = current_user.email

    # Send confirmation email before deletion (best effort)
    try:
        from app.services.email_service import send_email

        send_email(
            original_email,
            "BookSwipe — Account Deleted",
            f"<p>Your BookSwipe account ({original_email}) has been deleted "
            f"and your personal data has been anonymized.</p>"
            f"<p>If you did not request this, please contact us at "
            f"support@bookswipe.app.</p>",
        )
    except Exception:
        logger.warning("Failed to send account deletion email to %s", original_email)

    repo = UserRepository(db)
    repo.soft_delete(current_user)
    return MessageResponse(message="Account deleted. Your personal data has been anonymized.")


@router.get("/privacy-consent", response_model=PrivacyConsentResponse)
def get_privacy_consent(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the current user's privacy/analytics consent status."""
    from app.models import PrivacyConsent

    consent = db.query(PrivacyConsent).filter(PrivacyConsent.user_id == current_user.id).first()
    if not consent:
        return PrivacyConsentResponse(analytics_consent=False, marketing_consent=False, consent_date=None)
    return PrivacyConsentResponse(
        analytics_consent=consent.analytics_consent,
        marketing_consent=consent.marketing_consent,
        consent_date=consent.updated_at.isoformat() if consent.updated_at else None,
    )


@router.put("/privacy-consent", response_model=PrivacyConsentResponse)
def update_privacy_consent(
    body: PrivacyConsentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's privacy/analytics consent."""
    import datetime
    from app.models import PrivacyConsent

    consent = db.query(PrivacyConsent).filter(PrivacyConsent.user_id == current_user.id).first()
    now = datetime.datetime.now(datetime.timezone.utc)
    if not consent:
        consent = PrivacyConsent(
            user_id=current_user.id,
            analytics_consent=body.analytics_consent,
            marketing_consent=body.marketing_consent,
            updated_at=now,
        )
        db.add(consent)
    else:
        consent.analytics_consent = body.analytics_consent
        consent.marketing_consent = body.marketing_consent
        consent.updated_at = now
    db.commit()
    return PrivacyConsentResponse(
        analytics_consent=consent.analytics_consent,
        marketing_consent=consent.marketing_consent,
        consent_date=now.isoformat(),
    )


@router.get("/export-data")
def export_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Export all user data as JSON (GDPR right to data portability)."""
    from app.models import LikedBook, SwipeEvent, BookList, BookListItem, ActivityEvent, BookReview, PrivacyConsent

    liked = db.query(LikedBook).filter(LikedBook.user_id == current_user.id).all()
    swipes = db.query(SwipeEvent).filter(SwipeEvent.user_id == current_user.id).all()
    lists = db.query(BookList).filter(BookList.user_id == current_user.id).all()
    activities = db.query(ActivityEvent).filter(ActivityEvent.user_id == current_user.id).all()
    consent = db.query(PrivacyConsent).filter(PrivacyConsent.user_id == current_user.id).first()

    # Gather list items
    list_data = []
    for bl in lists:
        items = db.query(BookListItem).filter(BookListItem.list_id == bl.id).all()
        list_data.append({
            "id": bl.id,
            "name": bl.name,
            "description": bl.description,
            "is_public": bl.is_public,
            "created_at": bl.created_at.isoformat() if bl.created_at else None,
            "items": [{"google_book_id": i.google_book_id, "position": i.position} for i in items],
        })

    # Try to get reviews if the model exists
    reviews_data = []
    try:
        reviews = db.query(BookReview).filter(BookReview.user_id == current_user.id).all()
        reviews_data = [
            {
                "id": r.id,
                "google_book_id": r.google_book_id,
                "rating": r.rating,
                "text": r.review_text,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reviews
        ]
    except Exception:
        pass

    return {
        "profile": {
            "id": current_user.id,
            "email": current_user.email,
            "auth_provider": current_user.auth_provider,
            "role": current_user.role,
            "subscription_status": current_user.subscription_status,
            "subscription_plan": current_user.subscription_plan,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "liked_books": [
            {"google_book_id": lb.google_book_id, "liked_at": lb.liked_at.isoformat() if lb.liked_at else None}
            for lb in liked
        ],
        "swipe_events": [
            {
                "google_book_id": se.google_book_id,
                "action": se.action,
                "created_at": se.created_at.isoformat() if se.created_at else None,
            }
            for se in swipes
        ],
        "book_lists": list_data,
        "reviews": reviews_data,
        "activity": [
            {
                "event_type": ae.event_type,
                "created_at": ae.created_at.isoformat() if ae.created_at else None,
            }
            for ae in activities
        ],
        "privacy_consent": {
            "analytics_consent": consent.analytics_consent if consent else None,
            "marketing_consent": consent.marketing_consent if consent else None,
        },
    }
