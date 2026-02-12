"""Categories router for listing and retrieving book categories."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.category_repository import CategoryRepository, get_category_repository
from app.schemas import CategoryResponse
from app.services.category_service import CategoryService, get_category_service

router = APIRouter(prefix="/api/categories", tags=["categories"])


def _get_category_repo(db: Session = Depends(get_db)) -> CategoryRepository:
    """Provide a CategoryRepository via dependency injection.

    Args:
        db: SQLAlchemy database session.

    Returns:
        A CategoryRepository instance.
    """
    return get_category_repository(db)


def _get_category_service(
    repo: CategoryRepository = Depends(_get_category_repo),
) -> CategoryService:
    """Provide a CategoryService via dependency injection.

    Args:
        repo: The category repository.

    Returns:
        A CategoryService instance.
    """
    return get_category_service(repo)


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    service: CategoryService = Depends(_get_category_service),
) -> list:
    """Get all available book categories.

    Args:
        service: The category service for business logic.

    Returns:
        List of all categories sorted by name.
    """
    return service.list_categories()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    service: CategoryService = Depends(_get_category_service),
) -> CategoryResponse:
    """Get a single category by ID.

    Args:
        category_id: The category's primary key.
        service: The category service for business logic.

    Returns:
        The requested category.
    """
    return service.get_category(category_id)
