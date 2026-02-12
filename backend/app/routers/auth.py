"""Authentication endpoints: register, login, logout, refresh, profile."""

import datetime

from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import AuthError, ConflictError
from app.models import User
from app.schemas import (
    MessageResponse,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    check_password_strength,
)
from app.services.auth import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    oauth2_scheme,
    verify_password,
)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, body: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account and return access/refresh tokens."""
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise ConflictError(message="Email already registered")
    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    strength = check_password_strength(body.password)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        password_strength=strength,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, body: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return access/refresh tokens."""
    user = db.query(User).filter(User.email == body.email, User.is_active.is_(True)).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise AuthError(message="Invalid email or password")
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Invalidate the current access token by blacklisting it."""
    if token:
        blacklist_token(token, db)
    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
def refresh_token(request: Request, body: TokenRefresh, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access/refresh token pair."""
    user_id = decode_token(body.refresh_token, expected_type="refresh", db=db)
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise AuthError(message="User not found")
    # Rotate: blacklist old refresh token, issue new pair
    blacklist_token(body.refresh_token, db)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.delete("/me", response_model=MessageResponse)
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Soft-delete the authenticated user's account (GDPR compliant)."""
    current_user.is_active = False
    current_user.deleted_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    return MessageResponse(message="Account deleted")
