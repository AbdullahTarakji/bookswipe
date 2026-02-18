"""Reviews router: book reviews, ratings, helpful votes, and moderation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models import User
from app.repositories.review_repository import ReviewRepository
from app.schemas import (
    BookRatingStats,
    MessageResponse,
    PaginatedReviews,
    ReviewCreate,
    ReviewResponse,
    ReviewUpdate,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["reviews"])


def _username_from_user(user: User) -> str:
    """Derive display name from user email."""
    return user.email.split("@")[0]


def _build_review_response(
    review, username: str = "", user_has_voted: bool = False
) -> ReviewResponse:
    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        username=username,
        google_book_id=review.google_book_id,
        rating=review.rating,
        review_text=review.review_text,
        is_flagged=review.is_flagged,
        helpful_count=review.helpful_count,
        user_has_voted=user_has_voted,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


# --- Reviews CRUD ---


@router.post(
    "/books/{google_book_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_or_update_review(
    google_book_id: str,
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update a review for a book (upsert)."""
    repo = ReviewRepository(db)
    existing = repo.get_user_review(current_user.id, google_book_id)
    if existing:
        review = repo.update_review(existing, rating=body.rating, review_text=body.review_text)
    else:
        review = repo.create_review(
            user_id=current_user.id,
            google_book_id=google_book_id,
            rating=body.rating,
            review_text=body.review_text,
        )
    return _build_review_response(review, username=_username_from_user(current_user))


@router.get("/books/{google_book_id}/reviews", response_model=PaginatedReviews)
def get_book_reviews(
    google_book_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    sort_by: str = Query("newest", pattern=r"^(newest|helpful)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return paginated reviews for a book."""
    repo = ReviewRepository(db)
    reviews, total = repo.get_book_reviews(google_book_id, page, page_size, sort_by)
    avg_rating, total_ratings = repo.get_average_rating(google_book_id)

    review_ids = [r.id for r in reviews]
    voted_ids = repo.get_user_voted_review_ids(current_user.id, review_ids)

    return PaginatedReviews(
        reviews=[
            _build_review_response(
                r,
                username=_username_from_user(r.user) if r.user else "",
                user_has_voted=r.id in voted_ids,
            )
            for r in reviews
        ],
        total=total,
        page=page,
        page_size=page_size,
        average_rating=avg_rating,
        total_ratings=total_ratings,
    )


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    body: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update own review."""
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    if review.user_id != current_user.id:
        raise ForbiddenError("Cannot edit another user's review")
    update_data = body.model_dump(exclude_unset=True)
    if update_data:
        review = repo.update_review(review, **update_data)
    return _build_review_response(review, username=_username_from_user(current_user))


@router.delete("/reviews/{review_id}", response_model=MessageResponse)
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete own review (or admin can delete any)."""
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    if review.user_id != current_user.id and current_user.role != "admin":
        raise ForbiddenError("Cannot delete another user's review")
    repo.delete_review(review)
    return MessageResponse(message="Review deleted")


# --- Rating Stats ---


@router.get("/books/{google_book_id}/ratings", response_model=BookRatingStats)
def get_book_ratings(
    google_book_id: str,
    db: Session = Depends(get_db),
):
    """Return aggregated rating stats for a book (public)."""
    repo = ReviewRepository(db)
    avg_rating, total_ratings = repo.get_average_rating(google_book_id)
    distribution = repo.get_rating_distribution(google_book_id)
    return BookRatingStats(
        average_rating=avg_rating,
        total_ratings=total_ratings,
        rating_distribution=distribution,
    )


# --- Helpful Votes ---


@router.post("/reviews/{review_id}/vote", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def vote_helpful(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Vote a review as helpful."""
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    if review.user_id == current_user.id:
        raise ValidationError("Cannot vote on your own review")
    existing = repo.get_vote(current_user.id, review_id)
    if existing:
        raise ValidationError("Already voted on this review")
    repo.create_vote(current_user.id, review_id)
    return MessageResponse(message="Vote recorded")


@router.delete("/reviews/{review_id}/vote", response_model=MessageResponse)
def remove_vote(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove helpful vote from a review."""
    repo = ReviewRepository(db)
    vote = repo.get_vote(current_user.id, review_id)
    if not vote:
        raise NotFoundError("Vote not found")
    repo.delete_vote(vote)
    return MessageResponse(message="Vote removed")


# --- Admin Moderation ---


@router.post("/admin/reviews/{review_id}/flag", response_model=ReviewResponse)
def flag_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Flag a review (admin only)."""
    if current_user.role != "admin":
        raise ForbiddenError("Admin access required")
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    review = repo.flag_review(review, flagged=True)
    return _build_review_response(review, username=_username_from_user(review.user) if review.user else "")


@router.post("/admin/reviews/{review_id}/unflag", response_model=ReviewResponse)
def unflag_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unflag a review (admin only)."""
    if current_user.role != "admin":
        raise ForbiddenError("Admin access required")
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    review = repo.flag_review(review, flagged=False)
    return _build_review_response(review, username=_username_from_user(review.user) if review.user else "")
