"""Book discovery, liking, skipping, and detail endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import ConflictError, NotFoundError
from app.models import LikedBook, SkippedBook, User
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
    """Return paginated books from Google Books, excluding already-seen ones."""
    exclude_ids: set[str] = set()
    user_id: int | None = None
    if current_user:
        user_id = current_user.id
        liked_ids = db.query(LikedBook.google_book_id).filter(
            LikedBook.user_id == current_user.id
        ).all()
        skipped_ids = db.query(SkippedBook.google_book_id).filter(
            SkippedBook.user_id == current_user.id
        ).all()
        exclude_ids = {row[0] for row in liked_ids} | {row[0] for row in skipped_ids}

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
    """Return the authenticated user's liked books, paginated."""
    query = db.query(LikedBook).filter(LikedBook.user_id == current_user.id)
    total = query.count()
    books = (
        query.order_by(LikedBook.liked_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedLikedBooks(books=books, total=total, page=page, page_size=page_size)


@router.get("/{book_id}", response_model=BookDetail)
async def get_book_detail(
    book_id: str,
    current_user: User | None = Depends(get_optional_user),
):
    """Return detailed information about a single book by Google Books ID."""
    user_id = current_user.id if current_user else None
    return await get_book_by_id(book_id, user_id=user_id)


@router.post("/like", response_model=LikedBookResponse, status_code=status.HTTP_201_CREATED)
def like_book(
    body: BookAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a book to the authenticated user's liked collection."""
    existing = (
        db.query(LikedBook)
        .filter(
            LikedBook.user_id == current_user.id,
            LikedBook.google_book_id == body.google_book_id,
        )
        .first()
    )
    if existing:
        raise ConflictError(message="Book already liked")
    liked = LikedBook(
        user_id=current_user.id,
        google_book_id=body.google_book_id,
        title=body.title,
        authors=body.authors,
        thumbnail=body.thumbnail,
    )
    db.add(liked)
    db.commit()
    db.refresh(liked)
    return liked


@router.post("/skip", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def skip_book(
    body: BookAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record that the authenticated user skipped a book."""
    existing = (
        db.query(SkippedBook)
        .filter(
            SkippedBook.user_id == current_user.id,
            SkippedBook.google_book_id == body.google_book_id,
        )
        .first()
    )
    if existing:
        return MessageResponse(message="Book already skipped")
    skipped = SkippedBook(
        user_id=current_user.id,
        google_book_id=body.google_book_id,
    )
    db.add(skipped)
    db.commit()
    return MessageResponse(message="Book skipped")


@router.delete("/liked/{google_book_id}", response_model=MessageResponse)
def unlike_book(
    google_book_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a book from the authenticated user's liked collection."""
    liked = (
        db.query(LikedBook)
        .filter(
            LikedBook.user_id == current_user.id,
            LikedBook.google_book_id == google_book_id,
        )
        .first()
    )
    if not liked:
        raise NotFoundError(message="Liked book not found")
    db.delete(liked)
    db.commit()
    return MessageResponse(message="Book removed from liked list")
