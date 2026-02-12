"""Repository for book-related database operations."""

from sqlalchemy.orm import Session

from app.models import LikedBook, SkippedBook


class BookRepository:
    """Encapsulates all database access for LikedBook and SkippedBook models."""

    def __init__(self, db: Session) -> None:
        """Initialize with a database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def get_excluded_book_ids(self, user_id: int) -> set[str]:
        """Get all Google Book IDs that a user has liked or skipped.

        Args:
            user_id: The user's primary key.

        Returns:
            A set of Google Book ID strings to exclude from discovery.
        """
        liked_ids = (
            self.db.query(LikedBook.google_book_id)
            .filter(LikedBook.user_id == user_id)
            .all()
        )
        skipped_ids = (
            self.db.query(SkippedBook.google_book_id)
            .filter(SkippedBook.user_id == user_id)
            .all()
        )
        return {row[0] for row in liked_ids} | {row[0] for row in skipped_ids}

    def get_liked_books_paginated(
        self, user_id: int, page: int, page_size: int
    ) -> tuple[list[LikedBook], int]:
        """Get a paginated list of a user's liked books.

        Args:
            user_id: The user's primary key.
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            A tuple of (liked books list, total count).
        """
        query = self.db.query(LikedBook).filter(LikedBook.user_id == user_id)
        total = query.count()
        books = (
            query.order_by(LikedBook.liked_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return books, total

    def find_liked_book(self, user_id: int, google_book_id: str) -> LikedBook | None:
        """Find a specific liked book for a user.

        Args:
            user_id: The user's primary key.
            google_book_id: The Google Books API volume ID.

        Returns:
            The LikedBook if found, otherwise None.
        """
        return (
            self.db.query(LikedBook)
            .filter(
                LikedBook.user_id == user_id,
                LikedBook.google_book_id == google_book_id,
            )
            .first()
        )

    def create_liked_book(
        self,
        user_id: int,
        google_book_id: str,
        title: str,
        authors: str,
        thumbnail: str,
    ) -> LikedBook:
        """Create a new liked book record.

        Args:
            user_id: The user's primary key.
            google_book_id: The Google Books API volume ID.
            title: The book title.
            authors: Comma-separated author names.
            thumbnail: URL to the book's thumbnail image.

        Returns:
            The newly created LikedBook.
        """
        liked = LikedBook(
            user_id=user_id,
            google_book_id=google_book_id,
            title=title,
            authors=authors,
            thumbnail=thumbnail,
        )
        self.db.add(liked)
        self.db.commit()
        self.db.refresh(liked)
        return liked

    def find_skipped_book(self, user_id: int, google_book_id: str) -> SkippedBook | None:
        """Find a specific skipped book for a user.

        Args:
            user_id: The user's primary key.
            google_book_id: The Google Books API volume ID.

        Returns:
            The SkippedBook if found, otherwise None.
        """
        return (
            self.db.query(SkippedBook)
            .filter(
                SkippedBook.user_id == user_id,
                SkippedBook.google_book_id == google_book_id,
            )
            .first()
        )

    def create_skipped_book(self, user_id: int, google_book_id: str) -> SkippedBook:
        """Create a new skipped book record.

        Args:
            user_id: The user's primary key.
            google_book_id: The Google Books API volume ID.

        Returns:
            The newly created SkippedBook.
        """
        skipped = SkippedBook(
            user_id=user_id,
            google_book_id=google_book_id,
        )
        self.db.add(skipped)
        self.db.commit()
        return skipped

    def delete_liked_book(self, liked_book: LikedBook) -> None:
        """Remove a liked book record from the database.

        Args:
            liked_book: The LikedBook instance to delete.
        """
        self.db.delete(liked_book)
        self.db.commit()


def get_book_repository(db: Session) -> BookRepository:
    """FastAPI dependency that provides a BookRepository.

    Args:
        db: SQLAlchemy database session.

    Returns:
        A BookRepository instance.
    """
    return BookRepository(db)
