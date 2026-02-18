"""Repository for book review database operations."""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import BookReview, ReviewVote


class ReviewRepository:
    """Encapsulates database queries for book reviews and votes."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Reviews ---

    def get_review(self, review_id: int) -> BookReview | None:
        """Return a review by ID."""
        return self.db.query(BookReview).filter(BookReview.id == review_id).first()

    def get_user_review(self, user_id: int, google_book_id: str) -> BookReview | None:
        """Return a user's review for a specific book."""
        return (
            self.db.query(BookReview)
            .filter(BookReview.user_id == user_id, BookReview.google_book_id == google_book_id)
            .first()
        )

    def create_review(self, user_id: int, google_book_id: str, rating: int, review_text: str = "") -> BookReview:
        """Create a new review."""
        review = BookReview(
            user_id=user_id,
            google_book_id=google_book_id,
            rating=rating,
            review_text=review_text,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def update_review(self, review: BookReview, **kwargs: object) -> BookReview:
        """Update review fields."""
        for key, value in kwargs.items():
            if value is not None:
                setattr(review, key, value)
        self.db.commit()
        self.db.refresh(review)
        return review

    def delete_review(self, review: BookReview) -> None:
        """Delete a review."""
        self.db.delete(review)
        self.db.commit()

    def get_book_reviews(
        self,
        google_book_id: str,
        page: int,
        page_size: int,
        sort_by: str = "newest",
    ) -> tuple[list[BookReview], int]:
        """Return paginated reviews for a book."""
        query = self.db.query(BookReview).filter(
            BookReview.google_book_id == google_book_id,
            BookReview.is_flagged.is_(False),
        )
        total = query.count()

        if sort_by == "helpful":
            query = query.order_by(BookReview.helpful_count.desc(), BookReview.created_at.desc())
        else:
            query = query.order_by(BookReview.created_at.desc())

        reviews = query.offset((page - 1) * page_size).limit(page_size).all()
        return reviews, total

    def get_average_rating(self, google_book_id: str) -> tuple[float | None, int]:
        """Return (average_rating, total_ratings) for a book."""
        result = (
            self.db.query(
                func.avg(BookReview.rating),
                func.count(BookReview.id),
            )
            .filter(BookReview.google_book_id == google_book_id, BookReview.is_flagged.is_(False))
            .first()
        )
        avg_rating = round(float(result[0]), 2) if result[0] else None
        total = result[1] or 0
        return avg_rating, total

    def get_rating_distribution(self, google_book_id: str) -> dict[str, int]:
        """Return rating distribution {1: count, 2: count, ...}."""
        rows = (
            self.db.query(BookReview.rating, func.count(BookReview.id))
            .filter(BookReview.google_book_id == google_book_id, BookReview.is_flagged.is_(False))
            .group_by(BookReview.rating)
            .all()
        )
        return {str(r): c for r, c in rows}

    # --- Votes ---

    def get_vote(self, user_id: int, review_id: int) -> ReviewVote | None:
        """Return a user's vote on a review."""
        return (
            self.db.query(ReviewVote)
            .filter(ReviewVote.user_id == user_id, ReviewVote.review_id == review_id)
            .first()
        )

    def create_vote(self, user_id: int, review_id: int) -> ReviewVote:
        """Create a helpful vote and increment the review's count."""
        vote = ReviewVote(user_id=user_id, review_id=review_id)
        self.db.add(vote)
        review = self.get_review(review_id)
        if review:
            review.helpful_count = (review.helpful_count or 0) + 1
        self.db.commit()
        self.db.refresh(vote)
        return vote

    def delete_vote(self, vote: ReviewVote) -> None:
        """Remove a helpful vote and decrement the review's count."""
        review = self.get_review(vote.review_id)
        if review and review.helpful_count > 0:
            review.helpful_count -= 1
        self.db.delete(vote)
        self.db.commit()

    def get_user_voted_review_ids(self, user_id: int, review_ids: list[int]) -> set[int]:
        """Return set of review IDs the user has voted on."""
        if not review_ids:
            return set()
        rows = (
            self.db.query(ReviewVote.review_id)
            .filter(ReviewVote.user_id == user_id, ReviewVote.review_id.in_(review_ids))
            .all()
        )
        return {row[0] for row in rows}

    # --- Admin ---

    def flag_review(self, review: BookReview, flagged: bool = True) -> BookReview:
        """Flag or unflag a review."""
        review.is_flagged = flagged
        self.db.commit()
        self.db.refresh(review)
        return review
