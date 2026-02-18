"""Reviews router: book reviews, ratings, helpful votes, and admin moderation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models import User
from app.repositories.review_repository import ReviewRepository
from app.schemas import (
    MessageResponse,
    PaginatedReviews,
    ReviewCreate,
    ReviewFlagRequest,
    ReviewResponse,
    ReviewUpdate,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["reviews"])


def _username_from_user(user: User) -> str:
    return user.email.split("@")[0]


def _build_review_response(review, username: str = "", user_has_voted: bool = False) -> ReviewResponse:
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


# --- Create / Upsert Review ---


@router.post("/books/{book_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_or_update_review(
    book_id: str,
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update a review for a book (upsert: one review per user per book)."""
    repo = ReviewRepository(db)
    existing = repo.get_user_review(current_user.id, book_id)
    if existing:
        review = repo.update_review(existing, rating=body.rating, review_text=body.review_text)
    else:
        review = repo.create_review(current_user.id, book_id, body.rating, body.review_text)
    return _build_review_response(review, _username_from_user(current_user))


# --- Get Reviews for a Book ---


@router.get("/books/{book_id}/reviews", response_model=PaginatedReviews)
def get_book_reviews(
    book_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    sort: str = Query("newest", pattern="^(newest|helpful)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return paginated reviews for a book, sorted by newest or most helpful."""
    repo = ReviewRepository(db)
    reviews, total = repo.get_reviews_for_book(book_id, page, page_size, sort=sort)
    avg_rating, total_ratings = repo.get_average_rating(book_id)

    review_ids = [r.id for r in reviews]
    voted_ids = repo.get_user_voted_review_ids(current_user.id, review_ids)

    # Resolve usernames
    user_map: dict[int, str] = {}
    for review in reviews:
        if review.user_id not in user_map:
            user = db.query(User).filter(User.id == review.user_id).first()
            user_map[review.user_id] = _username_from_user(user) if user else ""

    return PaginatedReviews(
        reviews=[
            _build_review_response(
                r,
                username=user_map.get(r.user_id, ""),
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


# --- Update Own Review ---


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    body: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the authenticated user's review."""
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    if review.user_id != current_user.id:
        raise ForbiddenError("Cannot edit another user's review")
    update_data = body.model_dump(exclude_unset=True)
    if update_data:
        review = repo.update_review(review, **update_data)
    return _build_review_response(review, _username_from_user(current_user))


# --- Delete Own Review ---


@router.delete("/reviews/{review_id}", response_model=MessageResponse)
def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete the authenticated user's review."""
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    if review.user_id != current_user.id and current_user.role != "admin":
        raise ForbiddenError("Cannot delete another user's review")
    repo.delete_review(review)
    return MessageResponse(message="Review deleted")


# --- Helpful Vote ---


@router.post("/reviews/{review_id}/helpful", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def vote_helpful(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a review as helpful (one vote per user per review)."""
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


@router.delete("/reviews/{review_id}/helpful", response_model=MessageResponse)
def remove_helpful_vote(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a helpful vote from a review."""
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
    body: ReviewFlagRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin: flag a review for moderation."""
    if current_user.role != "admin":
        raise ForbiddenError("Admin access required")
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    review = repo.flag_review(review, body.reason)
    return _build_review_response(review)


@router.delete("/admin/reviews/{review_id}/flag", response_model=ReviewResponse)
def unflag_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin: remove flag from a review."""
    if current_user.role != "admin":
        raise ForbiddenError("Admin access required")
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    review = repo.unflag_review(review)
    return _build_review_response(review)


@router.delete("/admin/reviews/{review_id}", response_model=MessageResponse)
def admin_delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin: delete any review."""
    if current_user.role != "admin":
        raise ForbiddenError("Admin access required")
    repo = ReviewRepository(db)
    review = repo.get_review(review_id)
    if not review:
        raise NotFoundError("Review not found")
    repo.delete_review(review)
    return MessageResponse(message="Review deleted by admin")
