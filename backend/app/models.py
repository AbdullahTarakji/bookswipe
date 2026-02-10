import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    liked_books: Mapped[list["LikedBook"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    skipped_books: Mapped[list["SkippedBook"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class LikedBook(Base):
    __tablename__ = "liked_books"
    __table_args__ = (UniqueConstraint("user_id", "google_book_id", name="uq_user_liked_book"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    google_book_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    authors: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    thumbnail: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    liked_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="liked_books")


class SkippedBook(Base):
    __tablename__ = "skipped_books"
    __table_args__ = (UniqueConstraint("user_id", "google_book_id", name="uq_user_skipped_book"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    google_book_id: Mapped[str] = mapped_column(String(50), nullable=False)
    skipped_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="skipped_books")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    google_category_key: Mapped[str] = mapped_column(String(100), nullable=False)


SEED_CATEGORIES = [
    {"name": "Fiction", "google_category_key": "fiction"},
    {"name": "Romance", "google_category_key": "romance"},
    {"name": "Mystery", "google_category_key": "mystery"},
    {"name": "Sci-Fi", "google_category_key": "science+fiction"},
    {"name": "Fantasy", "google_category_key": "fantasy"},
    {"name": "Thriller", "google_category_key": "thriller"},
    {"name": "Biography", "google_category_key": "biography"},
    {"name": "History", "google_category_key": "history"},
    {"name": "Self-Help", "google_category_key": "self-help"},
    {"name": "Science", "google_category_key": "science"},
    {"name": "Business", "google_category_key": "business"},
    {"name": "Poetry", "google_category_key": "poetry"},
    {"name": "Horror", "google_category_key": "horror"},
    {"name": "Comics", "google_category_key": "comics"},
]
