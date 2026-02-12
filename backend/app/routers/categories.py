"""Category listing endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import NotFoundError
from app.models import Category
from app.schemas import CategoryResponse

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)):
    """Return all book categories ordered by name."""
    return db.query(Category).order_by(Category.name).all()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Return a single category by its ID."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise NotFoundError(message="Category not found")
    return category
