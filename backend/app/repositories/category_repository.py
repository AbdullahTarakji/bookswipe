"""Repository for category-related database operations."""

from sqlalchemy.orm import Session

from app.models import Category


class CategoryRepository:
    """Encapsulates all database access for the Category model."""

    def __init__(self, db: Session) -> None:
        """Initialize with a database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def list_all(self) -> list[Category]:
        """Get all categories ordered by name.

        Returns:
            A list of all Category instances sorted alphabetically.
        """
        return self.db.query(Category).order_by(Category.name).all()

    def get_by_id(self, category_id: int) -> Category | None:
        """Find a category by its primary key.

        Args:
            category_id: The category's primary key.

        Returns:
            The Category if found, otherwise None.
        """
        return self.db.query(Category).filter(Category.id == category_id).first()


def get_category_repository(db: Session) -> CategoryRepository:
    """FastAPI dependency that provides a CategoryRepository.

    Args:
        db: SQLAlchemy database session.

    Returns:
        A CategoryRepository instance.
    """
    return CategoryRepository(db)
