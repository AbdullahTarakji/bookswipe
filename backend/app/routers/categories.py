"""Category router: list and retrieve book categories."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import NotFoundError
from app.repositories.category_repository import CategoryRepository
from app.schemas import CategoryResponse

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """Return all available book categories sorted alphabetically."""
    repo = CategoryRepository(db)
    return repo.list_all()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Return a single category by its ID."""
    repo = CategoryRepository(db)
    category = repo.get_by_id(category_id)
    if not category:
        raise NotFoundError("Category not found")
    return category
