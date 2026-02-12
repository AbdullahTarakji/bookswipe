"""Books router handling discovery, liking, skipping, and unlike operations."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.repositories.book_repository import BookRepository, get_book_repository
from app.schemas import (
    BookAction,
    BookDetail,
    LikedBookResponse,
    MessageResponse,
    PaginatedBooks,
    PaginatedLikedBooks,
)
from app.services.auth import get_current_user, get_optional_user
from app.services.book_service import BookService, get_book_service

router = APIRouter(prefix="/api/books", tags=["books"])


def _get_book_repo(db: Session = Depends(get_db)) -> BookRepository:
    """Provide a BookRepository via dependency injection.

    Args:
        db: SQLAlchemy database session.

    Returns:
        A BookRepository instance.
    """
    return get_book_repository(db)


def _get_book_service(repo: BookRepository = Depends(_get_book_repo)) -> BookService:
    """Provide a BookService via dependency injection.

    Args:
        repo: The book repository.

    Returns:
        A BookService instance.
    """
    return get_book_service(repo)


@router.get("/discover", response_model=PaginatedBooks)
async def discover_books(
    category: str = Query("fiction", min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=40),
    current_user: User | None = Depends(get_optional_user),
    service: BookService = Depends(_get_book_service),
) -> PaginatedBooks:
    """Discover books by category, excluding previously seen ones.

    Args:
        category: The book category to search.
        page: Page number for pagination.
        page_size: Number of results per page.
        current_user: The authenticated user, or None for guests.
        service: The book service for business logic.

    Returns:
        Paginated list of discovered books.
    """
    return await service.discover(category, page, page_size, current_user)


@router.get("/liked", response_model=PaginatedLikedBooks)
def get_liked_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(_get_book_service),
) -> PaginatedLikedBooks:
    """Get the authenticated user's liked books with pagination.

    Args:
        page: Page number for pagination.
        page_size: Number of results per page.
        current_user: The authenticated user.
        service: The book service for business logic.

    Returns:
        Paginated list of liked books.
    """
    return service.get_liked_books(current_user.id, page, page_size)


@router.get("/{book_id}", response_model=BookDetail)
async def get_book_detail(
    book_id: str,
    current_user: User | None = Depends(get_optional_user),
    service: BookService = Depends(_get_book_service),
) -> BookDetail:
    """Get detailed information for a specific book.

    Args:
        book_id: The Google Books API volume ID.
        current_user: The authenticated user, or None for guests.
        service: The book service for business logic.

    Returns:
        Full book details.
    """
    return await service.get_detail(book_id, current_user)


@router.post("/like", response_model=LikedBookResponse, status_code=status.HTTP_201_CREATED)
def like_book(
    body: BookAction,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(_get_book_service),
) -> LikedBookResponse:
    """Like a book for the authenticated user.

    Args:
        body: The book details to like.
        current_user: The authenticated user.
        service: The book service for business logic.

    Returns:
        The created liked book record.
    """
    return service.like_book(body, current_user.id)


@router.post("/skip", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def skip_book(
    body: BookAction,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(_get_book_service),
) -> MessageResponse:
    """Skip a book for the authenticated user.

    Args:
        body: The book action with the Google Book ID.
        current_user: The authenticated user.
        service: The book service for business logic.

    Returns:
        Message confirming the book was skipped.
    """
    return service.skip_book(body, current_user.id)


@router.delete("/liked/{google_book_id}", response_model=MessageResponse)
def unlike_book(
    google_book_id: str,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends(_get_book_service),
) -> MessageResponse:
    """Remove a book from the authenticated user's liked list.

    Args:
        google_book_id: The Google Books API volume ID.
        current_user: The authenticated user.
        service: The book service for business logic.

    Returns:
        Message confirming removal.
    """
    return service.unlike_book(google_book_id, current_user.id)
