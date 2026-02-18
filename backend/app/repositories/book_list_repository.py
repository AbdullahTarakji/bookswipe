"""Repository for book list database operations."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import BookList, BookListItem


class BookListRepository:
    """Encapsulates database queries for BookList and BookListItem models."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Lists ---

    def get_list(self, list_id: int) -> BookList | None:
        """Return a book list by ID, or None."""
        return self.db.query(BookList).filter(BookList.id == list_id).first()

    def get_user_lists(self, user_id: int, page: int, page_size: int) -> tuple[list[BookList], int]:
        """Return paginated book lists for a user."""
        query = self.db.query(BookList).filter(BookList.user_id == user_id)
        total = query.count()
        lists = (
            query.order_by(BookList.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return lists, total

    def get_public_user_lists(self, user_id: int, page: int, page_size: int) -> tuple[list[BookList], int]:
        """Return paginated public book lists for a user."""
        query = self.db.query(BookList).filter(BookList.user_id == user_id, BookList.is_public.is_(True))
        total = query.count()
        lists = (
            query.order_by(BookList.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return lists, total

    def get_public_lists(self, page: int, page_size: int) -> tuple[list[BookList], int]:
        """Return paginated public book lists from all users."""
        query = self.db.query(BookList).filter(BookList.is_public.is_(True))
        total = query.count()
        lists = (
            query.order_by(BookList.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return lists, total

    def create_list(self, user_id: int, name: str, description: str = "", is_public: bool = True) -> BookList:
        """Create a new book list."""
        book_list = BookList(
            user_id=user_id,
            name=name,
            description=description,
            is_public=is_public,
        )
        self.db.add(book_list)
        self.db.commit()
        self.db.refresh(book_list)
        return book_list

    def update_list(self, book_list: BookList, **kwargs: object) -> BookList:
        """Update book list fields and persist."""
        for key, value in kwargs.items():
            if value is not None:
                setattr(book_list, key, value)
        self.db.commit()
        self.db.refresh(book_list)
        return book_list

    def delete_list(self, book_list: BookList) -> None:
        """Delete a book list and all its items."""
        self.db.delete(book_list)
        self.db.commit()

    def get_item_count(self, list_id: int) -> int:
        """Return number of items in a book list."""
        return self.db.query(BookListItem).filter(BookListItem.list_id == list_id).count()

    def get_cover_thumbnails(self, list_id: int, limit: int = 4) -> list[str]:
        """Return up to `limit` thumbnail URLs from the first items in a list."""
        items = (
            self.db.query(BookListItem.thumbnail)
            .filter(BookListItem.list_id == list_id, BookListItem.thumbnail != "")
            .order_by(BookListItem.position, BookListItem.added_at)
            .limit(limit)
            .all()
        )
        return [row[0] for row in items]

    # --- Items ---

    def get_item(self, list_id: int, book_id: str) -> BookListItem | None:
        """Return a specific item in a list, or None."""
        return (
            self.db.query(BookListItem)
            .filter(BookListItem.list_id == list_id, BookListItem.book_id == book_id)
            .first()
        )

    def get_items(self, list_id: int) -> list[BookListItem]:
        """Return all items in a book list ordered by position."""
        return (
            self.db.query(BookListItem)
            .filter(BookListItem.list_id == list_id)
            .order_by(BookListItem.position, BookListItem.added_at)
            .all()
        )

    def get_next_position(self, list_id: int) -> int:
        """Return the next position value for a new item."""
        max_pos = (
            self.db.query(func.max(BookListItem.position))
            .filter(BookListItem.list_id == list_id)
            .scalar()
        )
        return (max_pos or 0) + 1

    def add_item(
        self, list_id: int, book_id: str, note: str = "",
        title: str = "", authors: str = "", thumbnail: str = "",
    ) -> BookListItem:
        """Add a book to a list."""
        position = self.get_next_position(list_id)
        item = BookListItem(
            list_id=list_id,
            book_id=book_id,
            title=title,
            authors=authors,
            thumbnail=thumbnail,
            note=note,
            position=position,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def remove_item(self, item: BookListItem) -> None:
        """Remove a book from a list."""
        self.db.delete(item)
        self.db.commit()

    def reorder_items(self, list_id: int, book_ids: list[str]) -> list[BookListItem]:
        """Reorder items in a list according to the given book_id order."""
        items = self.get_items(list_id)
        item_map = {item.book_id: item for item in items}
        for position, book_id in enumerate(book_ids):
            if book_id in item_map:
                item_map[book_id].position = position
        self.db.commit()
        return self.get_items(list_id)
