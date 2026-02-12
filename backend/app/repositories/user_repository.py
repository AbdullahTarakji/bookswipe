"""Repository for user-related database operations."""

import datetime

from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    """Encapsulates all database access for the User model."""

    def __init__(self, db: Session) -> None:
        """Initialize with a database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        """Find a user by email address.

        Args:
            email: The email to search for.

        Returns:
            The User if found, otherwise None.
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_active_by_email(self, email: str) -> User | None:
        """Find an active user by email address.

        Args:
            email: The email to search for.

        Returns:
            The active User if found, otherwise None.
        """
        return (
            self.db.query(User)
            .filter(User.email == email, User.is_active.is_(True))
            .first()
        )

    def get_active_by_id(self, user_id: int) -> User | None:
        """Find an active user by ID.

        Args:
            user_id: The user's primary key.

        Returns:
            The active User if found, otherwise None.
        """
        return (
            self.db.query(User)
            .filter(User.id == user_id, User.is_active.is_(True))
            .first()
        )

    def create(self, email: str, hashed_password: str) -> User:
        """Create a new user and persist to the database.

        Args:
            email: The user's email address.
            hashed_password: The bcrypt-hashed password.

        Returns:
            The newly created User.
        """
        user = User(email=email, hashed_password=hashed_password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def soft_delete(self, user: User) -> None:
        """Soft-delete a user by marking them inactive.

        Args:
            user: The user to deactivate.
        """
        user.is_active = False
        user.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        self.db.commit()


def get_user_repository(db: Session) -> UserRepository:
    """FastAPI dependency that provides a UserRepository.

    Args:
        db: SQLAlchemy database session.

    Returns:
        A UserRepository instance.
    """
    return UserRepository(db)
