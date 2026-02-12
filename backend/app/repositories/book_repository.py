"""Repository for book-related database operations (likes, skips)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import LikedBook, SkippedBook


class BookRepository:
    """Encapsulates all database queries for LikedBook and SkippedBook models."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_excluded_book_ids(self, user_id: int) -> set[str]:
        """Return the set of Google Book IDs the user has liked or skipped."""
        liked_ids = self.db.query(LikedBook.google_book_id).filter(
            LikedBook.user_id == user_id
        ).all()
        skipped_ids = self.db.query(SkippedBook.google_book_id).filter(
            SkippedBook.user_id == user_id
        ).all()
        return {row[0] for row in liked_ids} | {row[0] for row in skipped_ids}

    def get_liked_books(self, user_id: int, page: int, page_size: int) -> tuple[list[LikedBook], int]:
        """Return a paginated list of liked books and the total count."""
        query = self.db.query(LikedBook).filter(LikedBook.user_id == user_id)
        total = query.count()
        books = (
            query.order_by(LikedBook.liked_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return books, total

    def get_liked_book(self, user_id: int, google_book_id: str) -> LikedBook | None:
        """Return a specific liked book, or None."""
        return (
            self.db.query(LikedBook)
            .filter(LikedBook.user_id == user_id, LikedBook.google_book_id == google_book_id)
            .first()
        )

    def create_liked_book(self, user_id: int, google_book_id: str, title: str, authors: str, thumbnail: str) -> LikedBook:
        """Create and persist a new liked book record."""
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

    def get_skipped_book(self, user_id: int, google_book_id: str) -> SkippedBook | None:
        """Return a specific skipped book, or None."""
        return (
            self.db.query(SkippedBook)
            .filter(SkippedBook.user_id == user_id, SkippedBook.google_book_id == google_book_id)
            .first()
        )

    def create_skipped_book(self, user_id: int, google_book_id: str) -> SkippedBook:
        """Create and persist a new skipped book record."""
        skipped = SkippedBook(
            user_id=user_id,
            google_book_id=google_book_id,
        )
        self.db.add(skipped)
        self.db.commit()
        return skipped

    def delete_liked_book(self, liked: LikedBook) -> None:
        """Remove a liked book record."""
        self.db.delete(liked)
        self.db.commit()
