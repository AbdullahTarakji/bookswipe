"""Repository for category database operations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Category


class CategoryRepository:
    """Encapsulates all database queries for the Category model."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Category]:
        """Return all categories ordered by name."""
        return self.db.query(Category).order_by(Category.name).all()

    def get_by_id(self, category_id: int) -> Category | None:
        """Return a category by primary key, or None."""
        return self.db.query(Category).filter(Category.id == category_id).first()
