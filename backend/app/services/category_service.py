"""Service layer for category-related business logic."""

from fastapi import HTTPException, status

from app.models import Category
from app.repositories.category_repository import CategoryRepository


class CategoryService:
    """Handles category listing and retrieval business logic."""

    def __init__(self, repo: CategoryRepository) -> None:
        """Initialize with a category repository.

        Args:
            repo: The category repository for database access.
        """
        self.repo = repo

    def list_categories(self) -> list[Category]:
        """Get all categories sorted by name.

        Returns:
            A list of all categories.
        """
        return self.repo.list_all()

    def get_category(self, category_id: int) -> Category:
        """Get a single category by ID.

        Args:
            category_id: The category's primary key.

        Returns:
            The requested Category.

        Raises:
            HTTPException: 404 if the category is not found.
        """
        category = self.repo.get_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        return category


def get_category_service(repo: CategoryRepository) -> "CategoryService":
    """FastAPI dependency that provides a CategoryService.

    Args:
        repo: The category repository instance.

    Returns:
        A CategoryService instance.
    """
    return CategoryService(repo)
