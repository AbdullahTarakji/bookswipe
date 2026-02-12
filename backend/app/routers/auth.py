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
        if user.auth_provider == "email" or user.auth_provider != provider:
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
        raise AuthError("Invalid email or password")
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
        raise AuthError(str(e))
    repo = UserRepository(db)
    user = _get_or_create_oauth_user(
        repo,
        email=google_user["email"],
        provider="google",
        provider_id=google_user["sub"],
    )
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
        raise AuthError(str(e))
    repo = UserRepository(db)
    user = _get_or_create_oauth_user(
        repo,
        email=apple_user["email"],
        provider="apple",
        provider_id=apple_user["sub"],
    )
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
    """Soft-delete the authenticated user's account (GDPR compliance)."""
    repo = UserRepository(db)
    repo.soft_delete(current_user)
    return MessageResponse(message="Account deleted")
