"""Authentication router handling registration, login, logout, and profile."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.repositories.user_repository import UserRepository, get_user_repository
from app.schemas import (
    MessageResponse,
    TokenRefresh,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    oauth2_scheme,
)
from app.services.user_service import UserService, get_user_service

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/auth", tags=["auth"])


def _get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    """Provide a UserRepository via dependency injection.

    Args:
        db: SQLAlchemy database session.

    Returns:
        A UserRepository instance.
    """
    return get_user_repository(db)


def _get_user_service(repo: UserRepository = Depends(_get_user_repo)) -> UserService:
    """Provide a UserService via dependency injection.

    Args:
        repo: The user repository.

    Returns:
        A UserService instance.
    """
    return get_user_service(repo)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(
    request: Request,
    body: UserRegister,
    service: UserService = Depends(_get_user_service),
) -> TokenResponse:
    """Register a new user account.

    Args:
        request: The incoming HTTP request (required by rate limiter).
        body: Validated registration data.
        service: The user service for business logic.

    Returns:
        Token response with access and refresh tokens.
    """
    return service.register(body)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    body: UserLogin,
    service: UserService = Depends(_get_user_service),
) -> TokenResponse:
    """Authenticate a user with email and password.

    Args:
        request: The incoming HTTP request (required by rate limiter).
        body: Login credentials.
        service: The user service for business logic.

    Returns:
        Token response with access and refresh tokens.
    """
    return service.login(body.email, body.password)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Log out by blacklisting the current token.

    Args:
        request: The incoming HTTP request.
        token: The Bearer token to blacklist.
        db: Database session for token blacklisting.

    Returns:
        Message confirming logout.
    """
    if token:
        blacklist_token(token, db)
    return MessageResponse(message="Successfully logged out")


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("5/minute")
def refresh_token(
    request: Request,
    body: TokenRefresh,
    db: Session = Depends(get_db),
    repo: UserRepository = Depends(_get_user_repo),
) -> TokenResponse:
    """Refresh an access token using a valid refresh token.

    Args:
        request: The incoming HTTP request (required by rate limiter).
        body: The refresh token payload.
        db: Database session for token operations.
        repo: User repository for user lookup.

    Returns:
        Token response with new access and refresh tokens.
    """
    user_id = decode_token(body.refresh_token, expected_type="refresh", db=db)
    user = repo.get_active_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    # Rotate: blacklist old refresh token, issue new pair
    blacklist_token(body.refresh_token, db)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Get the current authenticated user's profile.

    Args:
        current_user: The authenticated user from the token.

    Returns:
        The user's profile information.
    """
    return current_user


@router.delete("/me", response_model=MessageResponse)
def delete_account(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(_get_user_service),
) -> MessageResponse:
    """Soft-delete the authenticated user's account.

    Args:
        current_user: The authenticated user from the token.
        service: The user service for business logic.

    Returns:
        Message confirming account deletion.
    """
    return service.delete_account(current_user)
