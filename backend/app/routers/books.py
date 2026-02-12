"""Book router: discovery, likes, skips, and book detail endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import NotFoundError, ValidationError
from app.models import User
from app.repositories.book_repository import BookRepository
from app.schemas import (
    BookAction,
    BookDetail,
    LikedBookResponse,
    MessageResponse,
    PaginatedBooks,
    PaginatedLikedBooks,
)
from app.services.auth import get_current_user, get_optional_user
from app.services.google_books import get_book_by_id, search_books

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("/discover", response_model=PaginatedBooks)
async def discover_books(
    category: str = Query("fiction", min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=40),
    current_user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Discover books by category, excluding already liked/skipped books."""
    exclude_ids: set[str] = set()
    user_id: int | None = None
    if current_user:
        user_id = current_user.id
        repo = BookRepository(db)
        exclude_ids = repo.get_excluded_book_ids(current_user.id)

    books, total = await search_books(
        category=category,
        page=page,
        page_size=page_size,
        exclude_ids=exclude_ids if exclude_ids else None,
        user_id=user_id,
    )
    return PaginatedBooks(books=books, total=total, page=page, page_size=page_size)


@router.get("/liked", response_model=PaginatedLikedBooks)
def get_liked_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a paginated list of the authenticated user's liked books."""
    repo = BookRepository(db)
    books, total = repo.get_liked_books(current_user.id, page, page_size)
    return PaginatedLikedBooks(books=books, total=total, page=page, page_size=page_size)


@router.get("/{book_id}", response_model=BookDetail)
async def get_book_detail(
    book_id: str,
    current_user: User | None = Depends(get_optional_user),
):
    """Fetch detailed information for a single book by Google Books ID."""
    user_id = current_user.id if current_user else None
    return await get_book_by_id(book_id, user_id=user_id)


@router.post("/like", response_model=LikedBookResponse, status_code=status.HTTP_201_CREATED)
def like_book(
    body: BookAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a book to the authenticated user's liked list."""
    repo = BookRepository(db)
    existing = repo.get_liked_book(current_user.id, body.google_book_id)
    if existing:
        raise ValidationError("Book already liked")
    liked = repo.create_liked_book(
        user_id=current_user.id,
        google_book_id=body.google_book_id,
        title=body.title,
        authors=body.authors,
        thumbnail=body.thumbnail,
    )
    return liked


@router.post("/skip", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def skip_book(
    body: BookAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a book as skipped for the authenticated user."""
    repo = BookRepository(db)
    existing = repo.get_skipped_book(current_user.id, body.google_book_id)
    if existing:
        return MessageResponse(message="Book already skipped")
    repo.create_skipped_book(user_id=current_user.id, google_book_id=body.google_book_id)
    return MessageResponse(message="Book skipped")


@router.delete("/liked/{google_book_id}", response_model=MessageResponse)
def unlike_book(
    google_book_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a book from the authenticated user's liked list."""
    repo = BookRepository(db)
    liked = repo.get_liked_book(current_user.id, google_book_id)
    if not liked:
        raise NotFoundError("Liked book not found")
    repo.delete_liked_book(liked)
    return MessageResponse(message="Book removed from liked list")
