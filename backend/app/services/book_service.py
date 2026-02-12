"""Service layer for book-related business logic."""

from fastapi import HTTPException, status

from app.models import User
from app.repositories.book_repository import BookRepository
from app.schemas import (
    BookAction,
    LikedBookResponse,
    MessageResponse,
    PaginatedBooks,
    PaginatedLikedBooks,
)
from app.services.google_books import get_book_by_id, search_books


class BookService:
    """Handles book discovery, liking, skipping, and unlike business logic."""

    def __init__(self, repo: BookRepository) -> None:
        """Initialize with a book repository.

        Args:
            repo: The book repository for database access.
        """
        self.repo = repo

    async def discover(
        self,
        category: str,
        page: int,
        page_size: int,
        current_user: User | None,
    ) -> PaginatedBooks:
        """Discover books, excluding ones the user has already seen.

        Args:
            category: The book category to search.
            page: Page number for pagination.
            page_size: Number of results per page.
            current_user: The authenticated user, or None for guests.

        Returns:
            Paginated list of book summaries.
        """
        exclude_ids: set[str] = set()
        user_id: int | None = None
        if current_user:
            user_id = current_user.id
            exclude_ids = self.repo.get_excluded_book_ids(current_user.id)

        books, total = await search_books(
            category=category,
            page=page,
            page_size=page_size,
            exclude_ids=exclude_ids if exclude_ids else None,
            user_id=user_id,
        )
        return PaginatedBooks(books=books, total=total, page=page, page_size=page_size)

    def get_liked_books(
        self, user_id: int, page: int, page_size: int
    ) -> PaginatedLikedBooks:
        """Get a paginated list of the user's liked books.

        Args:
            user_id: The user's primary key.
            page: Page number for pagination.
            page_size: Number of results per page.

        Returns:
            Paginated list of liked book responses.
        """
        books, total = self.repo.get_liked_books_paginated(user_id, page, page_size)
        return PaginatedLikedBooks(books=books, total=total, page=page, page_size=page_size)

    async def get_detail(self, book_id: str, current_user: User | None):
        """Get detailed information for a single book.

        Args:
            book_id: The Google Books API volume ID.
            current_user: The authenticated user, or None for guests.

        Returns:
            BookDetail with full book information.
        """
        user_id = current_user.id if current_user else None
        return await get_book_by_id(book_id, user_id=user_id)

    def like_book(self, body: BookAction, user_id: int) -> LikedBookResponse:
        """Like a book for the authenticated user.

        Args:
            body: The book action data with book details.
            user_id: The user's primary key.

        Returns:
            The created liked book response.

        Raises:
            HTTPException: 409 if the book is already liked.
        """
        existing = self.repo.find_liked_book(user_id, body.google_book_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Book already liked",
            )
        liked = self.repo.create_liked_book(
            user_id=user_id,
            google_book_id=body.google_book_id,
            title=body.title,
            authors=body.authors,
            thumbnail=body.thumbnail,
        )
        return liked

    def skip_book(self, body: BookAction, user_id: int) -> MessageResponse:
        """Skip a book for the authenticated user.

        Args:
            body: The book action data with the Google Book ID.
            user_id: The user's primary key.

        Returns:
            MessageResponse indicating the book was skipped.
        """
        existing = self.repo.find_skipped_book(user_id, body.google_book_id)
        if existing:
            return MessageResponse(message="Book already skipped")
        self.repo.create_skipped_book(user_id, body.google_book_id)
        return MessageResponse(message="Book skipped")

    def unlike_book(self, google_book_id: str, user_id: int) -> MessageResponse:
        """Remove a book from the user's liked list.

        Args:
            google_book_id: The Google Books API volume ID.
            user_id: The user's primary key.

        Returns:
            MessageResponse confirming removal.

        Raises:
            HTTPException: 404 if the liked book is not found.
        """
        liked = self.repo.find_liked_book(user_id, google_book_id)
        if not liked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Liked book not found",
            )
        self.repo.delete_liked_book(liked)
        return MessageResponse(message="Book removed from liked list")


def get_book_service(repo: BookRepository) -> "BookService":
    """FastAPI dependency that provides a BookService.

    Args:
        repo: The book repository instance.

    Returns:
        A BookService instance.
    """
    return BookService(repo)
