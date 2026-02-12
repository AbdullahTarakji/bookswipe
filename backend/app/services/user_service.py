"""Service layer for user-related business logic."""

from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.schemas import (
    MessageResponse,
    TokenResponse,
    UserRegister,
    check_password_strength,
)
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


class UserService:
    """Handles user registration, login, and account management business logic."""

    def __init__(self, repo: UserRepository) -> None:
        """Initialize with a user repository.

        Args:
            repo: The user repository for database access.
        """
        self.repo = repo

    def register(self, body: UserRegister) -> TokenResponse:
        """Register a new user account.

        Args:
            body: Validated registration data with email and password.

        Returns:
            TokenResponse with access and refresh tokens plus password strength.

        Raises:
            HTTPException: 409 if the email is already registered.
        """
        existing = self.repo.get_by_email(body.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        user = self.repo.create(body.email, hash_password(body.password))
        strength = check_password_strength(body.password)
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
            password_strength=strength,
        )

    def login(self, email: str, password: str) -> TokenResponse:
        """Authenticate a user with email and password.

        Args:
            email: The user's email address.
            password: The plaintext password to verify.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            HTTPException: 401 if credentials are invalid.
        """
        user = self.repo.get_active_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        return TokenResponse(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    def delete_account(self, user) -> MessageResponse:
        """Soft-delete a user account for GDPR compliance.

        Args:
            user: The authenticated user to deactivate.

        Returns:
            MessageResponse confirming deletion.
        """
        self.repo.soft_delete(user)
        return MessageResponse(message="Account deleted")


def get_user_service(repo: UserRepository) -> "UserService":
    """FastAPI dependency that provides a UserService.

    Args:
        repo: The user repository instance.

    Returns:
        A UserService instance.
    """
    return UserService(repo)
