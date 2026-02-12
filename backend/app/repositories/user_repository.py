"""Repository for User and authentication-related database operations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import BlacklistedToken, User


class UserRepository:
    """Encapsulates all database queries for User and token blacklist models."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str, active_only: bool = True) -> User | None:
        """Return a user matching the given email, or None."""
        query = self.db.query(User).filter(User.email == email)
        if active_only:
            query = query.filter(User.is_active.is_(True))
        return query.first()

    def get_by_id(self, user_id: int, active_only: bool = True) -> User | None:
        """Return a user by primary key, or None."""
        query = self.db.query(User).filter(User.id == user_id)
        if active_only:
            query = query.filter(User.is_active.is_(True))
        return query.first()

    def create(
        self, email: str, hashed_password: str,
        auth_provider: str = "email", provider_id: str | None = None,
    ) -> User:
        """Create and persist a new user."""
        user = User(
            email=email,
            hashed_password=hashed_password,
            auth_provider=auth_provider,
            provider_id=provider_id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_provider(self, user: User, provider: str, provider_id: str) -> None:
        """Update the OAuth provider info on an existing user."""
        user.auth_provider = provider
        user.provider_id = provider_id
        self.db.commit()

    def soft_delete(self, user: User) -> None:
        """Soft-delete a user for GDPR compliance."""
        import datetime

        user.is_active = False
        user.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        self.db.commit()

    def is_token_blacklisted(self, jti: str) -> bool:
        """Check whether a JWT ID has been revoked."""
        return self.db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first() is not None

    def blacklist_token(self, jti: str) -> None:
        """Add a JWT ID to the blacklist."""
        existing = self.db.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).first()
        if not existing:
            self.db.add(BlacklistedToken(jti=jti))
            self.db.commit()
