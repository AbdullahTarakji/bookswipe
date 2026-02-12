"""Seed script for BookSwipe demo data.

Creates demo users, sample liked/skipped books, swipe history,
and user preferences for a realistic demonstration environment.

Usage:
    python -m scripts.seed_demo          # from backend/
    docker compose exec backend python -m scripts.seed_demo
"""

import json
import sys
import os

# Ensure the backend package is importable when run from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import (
    Category,
    LikedBook,
    Notification,
    NotificationPreference,
    SEED_CATEGORIES,
    SkippedBook,
    SwipeEvent,
    User,
    UserPreference,
)
from app.services.auth import hash_password


# ---------------------------------------------------------------------------
# Demo users
# ---------------------------------------------------------------------------
DEMO_USERS = [
    {
        "email": "admin@bookswipe.app",
        "password": "Admin123!",
        "role": "admin",
    },
    {
        "email": "reader1@bookswipe.app",
        "password": "Reader123!",
        "role": "user",
    },
    {
        "email": "reader2@bookswipe.app",
        "password": "Reader123!",
        "role": "user",
    },
]

# ---------------------------------------------------------------------------
# Sample books — realistic Google Books entries
# ---------------------------------------------------------------------------
SAMPLE_BOOKS = [
    {
        "google_book_id": "wrOQLV6xB-wC",
        "title": "The Hobbit",
        "authors": "J.R.R. Tolkien",
        "thumbnail": "https://books.google.com/books/content?id=wrOQLV6xB-wC&printsec=frontcover&img=1&zoom=1",
        "genre": "Fantasy",
        "category": "fantasy",
    },
    {
        "google_book_id": "aWZzLPhY4o0C",
        "title": "The Great Gatsby",
        "authors": "F. Scott Fitzgerald",
        "thumbnail": "https://books.google.com/books/content?id=aWZzLPhY4o0C&printsec=frontcover&img=1&zoom=1",
        "genre": "Fiction",
        "category": "fiction",
    },
    {
        "google_book_id": "PGR2AwAAQBAJ",
        "title": "To Kill a Mockingbird",
        "authors": "Harper Lee",
        "thumbnail": "https://books.google.com/books/content?id=PGR2AwAAQBAJ&printsec=frontcover&img=1&zoom=1",
        "genre": "Fiction",
        "category": "fiction",
    },
    {
        "google_book_id": "kotPYEqx7kMC",
        "title": "1984",
        "authors": "George Orwell",
        "thumbnail": "https://books.google.com/books/content?id=kotPYEqx7kMC&printsec=frontcover&img=1&zoom=1",
        "genre": "Sci-Fi",
        "category": "science+fiction",
    },
    {
        "google_book_id": "sazytgAACAAJ",
        "title": "Pride and Prejudice",
        "authors": "Jane Austen",
        "thumbnail": "https://books.google.com/books/content?id=sazytgAACAAJ&printsec=frontcover&img=1&zoom=1",
        "genre": "Romance",
        "category": "romance",
    },
    {
        "google_book_id": "k_IPcgAACAAJ",
        "title": "Dune",
        "authors": "Frank Herbert",
        "thumbnail": "https://books.google.com/books/content?id=k_IPcgAACAAJ&printsec=frontcover&img=1&zoom=1",
        "genre": "Sci-Fi",
        "category": "science+fiction",
    },
    {
        "google_book_id": "HCu3QQAACAAJ",
        "title": "The Shining",
        "authors": "Stephen King",
        "thumbnail": "https://books.google.com/books/content?id=HCu3QQAACAAJ&printsec=frontcover&img=1&zoom=1",
        "genre": "Horror",
        "category": "horror",
    },
    {
        "google_book_id": "1q_xAwAAQBAJ",
        "title": "Sapiens: A Brief History of Humankind",
        "authors": "Yuval Noah Harari",
        "thumbnail": "https://books.google.com/books/content?id=1q_xAwAAQBAJ&printsec=frontcover&img=1&zoom=1",
        "genre": "History",
        "category": "history",
    },
    {
        "google_book_id": "yng_CwAAQBAJ",
        "title": "Atomic Habits",
        "authors": "James Clear",
        "thumbnail": "https://books.google.com/books/content?id=yng_CwAAQBAJ&printsec=frontcover&img=1&zoom=1",
        "genre": "Self-Help",
        "category": "self-help",
    },
    {
        "google_book_id": "TCkFzgEACAAJ",
        "title": "The Da Vinci Code",
        "authors": "Dan Brown",
        "thumbnail": "https://books.google.com/books/content?id=TCkFzgEACAAJ&printsec=frontcover&img=1&zoom=1",
        "genre": "Thriller",
        "category": "thriller",
    },
]


def seed_categories(db: Session) -> None:
    """Ensure all default categories exist."""
    existing = {c.name for c in db.query(Category).all()}
    for cat in SEED_CATEGORIES:
        if cat["name"] not in existing:
            db.add(Category(**cat))
    db.commit()
    print(f"  Categories: {db.query(Category).count()} total")


def seed_users(db: Session) -> dict[str, User]:
    """Create demo users, returning a name->User mapping."""
    users: dict[str, User] = {}
    for info in DEMO_USERS:
        existing = db.query(User).filter(User.email == info["email"]).first()
        if existing:
            users[info["email"]] = existing
            print(f"  User {info['email']} already exists (id={existing.id})")
            continue
        user = User(
            email=info["email"],
            hashed_password=hash_password(info["password"]),
            role=info["role"],
            auth_provider="email",
        )
        db.add(user)
        db.flush()
        users[info["email"]] = user
        print(f"  Created user {info['email']} (id={user.id}, role={info['role']})")
    db.commit()
    return users


def seed_liked_books(db: Session, user: User, books: list[dict]) -> None:
    """Add liked books for a user."""
    for book in books:
        exists = (
            db.query(LikedBook)
            .filter(LikedBook.user_id == user.id, LikedBook.google_book_id == book["google_book_id"])
            .first()
        )
        if exists:
            continue
        db.add(
            LikedBook(
                user_id=user.id,
                google_book_id=book["google_book_id"],
                title=book["title"],
                authors=book["authors"],
                thumbnail=book["thumbnail"],
            )
        )
    db.commit()


def seed_skipped_books(db: Session, user: User, books: list[dict]) -> None:
    """Add skipped books for a user."""
    for book in books:
        exists = (
            db.query(SkippedBook)
            .filter(SkippedBook.user_id == user.id, SkippedBook.google_book_id == book["google_book_id"])
            .first()
        )
        if exists:
            continue
        db.add(
            SkippedBook(
                user_id=user.id,
                google_book_id=book["google_book_id"],
            )
        )
    db.commit()


def seed_swipe_events(db: Session, user: User, liked: list[dict], skipped: list[dict]) -> None:
    """Record swipe events for preference learning."""
    for book in liked:
        db.add(
            SwipeEvent(
                user_id=user.id,
                google_book_id=book["google_book_id"],
                action="like",
                genre=book.get("genre", ""),
                author=book.get("authors", ""),
                category=book.get("category", ""),
            )
        )
    for book in skipped:
        db.add(
            SwipeEvent(
                user_id=user.id,
                google_book_id=book["google_book_id"],
                action="skip",
                genre=book.get("genre", ""),
                author=book.get("authors", ""),
                category=book.get("category", ""),
            )
        )
    db.commit()


def seed_user_preferences(db: Session, user: User, liked: list[dict]) -> None:
    """Build a preference profile from liked books."""
    genre_scores: dict[str, float] = {}
    author_scores: dict[str, float] = {}
    category_scores: dict[str, float] = {}
    for book in liked:
        genre = book.get("genre", "")
        if genre:
            genre_scores[genre] = genre_scores.get(genre, 0) + 1.0
        author = book.get("authors", "")
        if author:
            author_scores[author] = author_scores.get(author, 0) + 1.0
        cat = book.get("category", "")
        if cat:
            category_scores[cat] = category_scores.get(cat, 0) + 1.0

    existing = db.query(UserPreference).filter(UserPreference.user_id == user.id).first()
    if existing:
        existing.genre_scores = json.dumps(genre_scores)
        existing.author_scores = json.dumps(author_scores)
        existing.category_scores = json.dumps(category_scores)
    else:
        db.add(
            UserPreference(
                user_id=user.id,
                genre_scores=json.dumps(genre_scores),
                author_scores=json.dumps(author_scores),
                category_scores=json.dumps(category_scores),
            )
        )
    db.commit()


def seed_notifications(db: Session, user: User) -> None:
    """Create sample notification preferences and history."""
    existing_pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user.id).first()
    if not existing_pref:
        db.add(NotificationPreference(user_id=user.id, recommendations=True, social=True, marketing=False))

    existing_notifs = db.query(Notification).filter(Notification.user_id == user.id).count()
    if existing_notifs == 0:
        db.add(
            Notification(
                user_id=user.id,
                title="Welcome to BookSwipe!",
                body="Start swiping to discover your next favorite read.",
                category="general",
                deep_link="/discover",
            )
        )
        db.add(
            Notification(
                user_id=user.id,
                title="New recommendations ready",
                body="Based on your reading taste, we found 5 new books you might love.",
                category="recommendations",
                deep_link="/discover",
            )
        )
    db.commit()


def main() -> None:
    """Run the full demo seed pipeline."""
    print("=" * 60)
    print("BookSwipe Demo Seed")
    print("=" * 60)

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("\n[1/6] Seeding categories...")
        seed_categories(db)

        print("\n[2/6] Seeding demo users...")
        users = seed_users(db)

        reader1 = users["reader1@bookswipe.app"]
        reader2 = users["reader2@bookswipe.app"]

        # reader1 likes fiction/fantasy, skips horror/thriller
        r1_liked = SAMPLE_BOOKS[:5]   # Hobbit, Gatsby, Mockingbird, 1984, Pride
        r1_skipped = SAMPLE_BOOKS[6:8]  # Shining, Sapiens

        # reader2 likes sci-fi/thriller, skips romance
        r2_liked = [SAMPLE_BOOKS[3], SAMPLE_BOOKS[5], SAMPLE_BOOKS[6], SAMPLE_BOOKS[9]]  # 1984, Dune, Shining, DaVinci
        r2_skipped = [SAMPLE_BOOKS[4], SAMPLE_BOOKS[8]]  # Pride, Atomic Habits

        print("\n[3/6] Seeding liked & skipped books...")
        seed_liked_books(db, reader1, r1_liked)
        seed_skipped_books(db, reader1, r1_skipped)
        seed_liked_books(db, reader2, r2_liked)
        seed_skipped_books(db, reader2, r2_skipped)
        print(f"  reader1: {len(r1_liked)} liked, {len(r1_skipped)} skipped")
        print(f"  reader2: {len(r2_liked)} liked, {len(r2_skipped)} skipped")

        print("\n[4/6] Seeding swipe events...")
        seed_swipe_events(db, reader1, r1_liked, r1_skipped)
        seed_swipe_events(db, reader2, r2_liked, r2_skipped)

        print("\n[5/6] Seeding user preferences...")
        seed_user_preferences(db, reader1, r1_liked)
        seed_user_preferences(db, reader2, r2_liked)

        print("\n[6/6] Seeding notifications...")
        seed_notifications(db, reader1)
        seed_notifications(db, reader2)

        print("\n" + "=" * 60)
        print("Demo seed complete!")
        print("=" * 60)
        print("\nDemo accounts:")
        print("  admin@bookswipe.app    / Admin123!   (admin)")
        print("  reader1@bookswipe.app  / Reader123!  (user)")
        print("  reader2@bookswipe.app  / Reader123!  (user)")
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
