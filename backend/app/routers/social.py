"""Social router: profiles, follows, book lists, activity feed, and user search."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models import User
from app.repositories.book_list_repository import BookListRepository
from app.repositories.social_repository import SocialRepository
from app.schemas import (
    ActivityEventResponse,
    BookListCreate,
    BookListDetailResponse,
    BookListItemAdd,
    BookListItemResponse,
    BookListReorder,
    BookListResponse,
    BookListUpdate,
    FollowResponse,
    MessageResponse,
    PaginatedActivityFeed,
    PaginatedBookLists,
    PaginatedFollows,
    UserProfileResponse,
    UserProfileUpdate,
    UserSearchResponse,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["social"])


def _username_from_user(user: User) -> str:
    """Derive display name from user email."""
    return user.email.split("@")[0]


def _build_profile_response(
    user: User,
    social_repo: SocialRepository,
    current_user_id: int | None = None,
) -> UserProfileResponse:
    """Build a UserProfileResponse from a User and their profile."""
    profile = social_repo.get_or_create_profile(user.id)
    is_following = False
    if current_user_id and current_user_id != user.id:
        is_following = social_repo.is_following(current_user_id, user.id)
    return UserProfileResponse(
        user_id=user.id,
        username=_username_from_user(user),
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        is_public=profile.is_public,
        reading_goal=profile.reading_goal,
        followers_count=social_repo.get_followers_count(user.id),
        following_count=social_repo.get_following_count(user.id),
        books_liked_count=social_repo.get_liked_books_count(user.id),
        is_following=is_following,
    )


# --- Profile ---


@router.get("/profile", response_model=UserProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's profile."""
    repo = SocialRepository(db)
    return _build_profile_response(current_user, repo, current_user.id)


@router.put("/profile", response_model=UserProfileResponse)
def update_my_profile(
    body: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the authenticated user's profile."""
    repo = SocialRepository(db)
    profile = repo.get_or_create_profile(current_user.id)
    update_data = body.model_dump(exclude_unset=True)
    if update_data:
        repo.update_profile(profile, **update_data)
    return _build_profile_response(current_user, repo, current_user.id)


@router.get("/profile/{user_id}", response_model=UserProfileResponse)
def get_user_profile(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a public user's profile."""
    target = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not target:
        raise NotFoundError("User not found")
    repo = SocialRepository(db)
    profile = repo.get_or_create_profile(user_id)
    if not profile.is_public and user_id != current_user.id:
        raise ForbiddenError("This profile is private")
    return _build_profile_response(target, repo, current_user.id)


# --- Follow / Unfollow ---


@router.post("/social/follow/{user_id}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Follow another user."""
    if user_id == current_user.id:
        raise ValidationError("Cannot follow yourself")
    target = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not target:
        raise NotFoundError("User not found")
    repo = SocialRepository(db)
    existing = repo.get_follow(current_user.id, user_id)
    if existing:
        raise ValidationError("Already following this user")
    repo.create_follow(current_user.id, user_id)
    repo.create_activity(
        current_user.id,
        "followed_user",
        {"followed_user_id": user_id, "followed_username": _username_from_user(target)},
    )
    return MessageResponse(message="Followed successfully")


@router.delete("/social/follow/{user_id}", response_model=MessageResponse)
def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unfollow a user."""
    repo = SocialRepository(db)
    follow = repo.get_follow(current_user.id, user_id)
    if not follow:
        raise NotFoundError("Not following this user")
    repo.delete_follow(follow)
    return MessageResponse(message="Unfollowed successfully")


@router.get("/social/followers", response_model=PaginatedFollows)
def get_followers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's followers."""
    repo = SocialRepository(db)
    users, total = repo.get_followers(current_user.id, page, page_size)
    following_ids = repo.get_following_ids(current_user.id)
    return PaginatedFollows(
        users=[
            FollowResponse(
                user_id=u.id,
                username=_username_from_user(u),
                is_following=u.id in following_ids,
            )
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/social/following", response_model=PaginatedFollows)
def get_following(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the users the authenticated user is following."""
    repo = SocialRepository(db)
    users, total = repo.get_following(current_user.id, page, page_size)
    return PaginatedFollows(
        users=[
            FollowResponse(
                user_id=u.id,
                username=_username_from_user(u),
                is_following=True,
            )
            for u in users
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# --- Activity Feed ---


@router.get("/social/feed", response_model=PaginatedActivityFeed)
def get_activity_feed(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the activity feed for the authenticated user (their activity + followed users)."""
    repo = SocialRepository(db)
    following_ids = repo.get_following_ids(current_user.id)
    feed_user_ids = list(following_ids | {current_user.id})
    events, total = repo.get_feed(feed_user_ids, page, page_size)
    return PaginatedActivityFeed(
        events=[
            ActivityEventResponse(
                id=e.id,
                user_id=e.user_id,
                username=_username_from_user(e.user) if e.user else "",
                event_type=e.event_type,
                metadata=json.loads(e.event_data) if isinstance(e.event_data, str) else e.event_data,
                created_at=e.created_at,
            )
            for e in events
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# --- User Search ---


@router.get("/social/search", response_model=UserSearchResponse)
def search_users(
    q: str = Query(..., min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search for users by name/email."""
    repo = SocialRepository(db)
    users, total = repo.search_users(q, page, page_size)
    following_ids = repo.get_following_ids(current_user.id)
    return UserSearchResponse(
        users=[
            FollowResponse(
                user_id=u.id,
                username=_username_from_user(u),
                is_following=u.id in following_ids,
            )
            for u in users
            if u.id != current_user.id
        ],
        total=total,
    )


# --- Book Lists ---


@router.post("/book-lists", response_model=BookListResponse, status_code=status.HTTP_201_CREATED)
def create_book_list(
    body: BookListCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new book list."""
    repo = BookListRepository(db)
    social_repo = SocialRepository(db)
    book_list = repo.create_list(
        user_id=current_user.id,
        name=body.name,
        description=body.description,
        is_public=body.is_public,
    )
    social_repo.create_activity(
        current_user.id,
        "created_list",
        {"list_id": book_list.id, "list_name": book_list.name},
    )
    return BookListResponse(
        id=book_list.id,
        user_id=book_list.user_id,
        name=book_list.name,
        description=book_list.description,
        is_public=book_list.is_public,
        created_at=book_list.created_at,
        item_count=0,
        owner_username=_username_from_user(current_user),
    )


@router.get("/book-lists", response_model=PaginatedBookLists)
def get_my_book_lists(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's book lists."""
    repo = BookListRepository(db)
    lists, total = repo.get_user_lists(current_user.id, page, page_size)
    return PaginatedBookLists(
        lists=[
            BookListResponse(
                id=bl.id,
                user_id=bl.user_id,
                name=bl.name,
                description=bl.description,
                is_public=bl.is_public,
                created_at=bl.created_at,
                item_count=repo.get_item_count(bl.id),
                owner_username=_username_from_user(current_user),
            )
            for bl in lists
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/book-lists/{list_id}", response_model=BookListDetailResponse)
def get_book_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a book list with its items."""
    repo = BookListRepository(db)
    book_list = repo.get_list(list_id)
    if not book_list:
        raise NotFoundError("Book list not found")
    if book_list.user_id != current_user.id and not book_list.is_public:
        raise ForbiddenError("This book list is private")
    owner = db.query(User).filter(User.id == book_list.user_id).first()
    items = repo.get_items(list_id)
    return BookListDetailResponse(
        id=book_list.id,
        user_id=book_list.user_id,
        name=book_list.name,
        description=book_list.description,
        is_public=book_list.is_public,
        created_at=book_list.created_at,
        item_count=len(items),
        owner_username=_username_from_user(owner) if owner else "",
        items=[BookListItemResponse.model_validate(item) for item in items],
    )


@router.put("/book-lists/{list_id}", response_model=BookListResponse)
def update_book_list(
    list_id: int,
    body: BookListUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a book list."""
    repo = BookListRepository(db)
    book_list = repo.get_list(list_id)
    if not book_list:
        raise NotFoundError("Book list not found")
    if book_list.user_id != current_user.id:
        raise ForbiddenError("Cannot update another user's list")
    update_data = body.model_dump(exclude_unset=True)
    if update_data:
        repo.update_list(book_list, **update_data)
    return BookListResponse(
        id=book_list.id,
        user_id=book_list.user_id,
        name=book_list.name,
        description=book_list.description,
        is_public=book_list.is_public,
        created_at=book_list.created_at,
        item_count=repo.get_item_count(book_list.id),
        owner_username=_username_from_user(current_user),
    )


@router.delete("/book-lists/{list_id}", response_model=MessageResponse)
def delete_book_list(
    list_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a book list."""
    repo = BookListRepository(db)
    book_list = repo.get_list(list_id)
    if not book_list:
        raise NotFoundError("Book list not found")
    if book_list.user_id != current_user.id:
        raise ForbiddenError("Cannot delete another user's list")
    repo.delete_list(book_list)
    return MessageResponse(message="Book list deleted")


@router.post(
    "/book-lists/{list_id}/books",
    response_model=BookListItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_book_to_list(
    list_id: int,
    body: BookListItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a book to a list."""
    repo = BookListRepository(db)
    book_list = repo.get_list(list_id)
    if not book_list:
        raise NotFoundError("Book list not found")
    if book_list.user_id != current_user.id:
        raise ForbiddenError("Cannot modify another user's list")
    existing = repo.get_item(list_id, body.book_id)
    if existing:
        raise ValidationError("Book already in list")
    item = repo.add_item(list_id, body.book_id, body.note)
    return BookListItemResponse.model_validate(item)


@router.delete("/book-lists/{list_id}/books/{book_id}", response_model=MessageResponse)
def remove_book_from_list(
    list_id: int,
    book_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a book from a list."""
    repo = BookListRepository(db)
    book_list = repo.get_list(list_id)
    if not book_list:
        raise NotFoundError("Book list not found")
    if book_list.user_id != current_user.id:
        raise ForbiddenError("Cannot modify another user's list")
    item = repo.get_item(list_id, book_id)
    if not item:
        raise NotFoundError("Book not in list")
    repo.remove_item(item)
    return MessageResponse(message="Book removed from list")
