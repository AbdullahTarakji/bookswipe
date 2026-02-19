"""Share router: deep link generation, OG meta serving, and short link resolution."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import NotFoundError
from app.models import User
from app.repositories.book_list_repository import BookListRepository
from app.repositories.social_repository import SocialRepository
from app.schemas import ShareResponse
from app.services.auth import get_current_user
from app.services.google_books import get_book_by_id
from app.services.share import (
    render_og_html,
    resolve_short_code,
    share_book,
    share_list,
    share_user,
)

router = APIRouter(tags=["share"])

# Social media bot user-agent patterns
_BOT_UA_PATTERN = re.compile(
    r"(facebookexternalhit|Twitterbot|LinkedInBot|Slackbot|WhatsApp|TelegramBot|Discordbot|Pinterest|Googlebot)",
    re.IGNORECASE,
)


def _is_bot(request: Request) -> bool:
    ua = request.headers.get("user-agent", "")
    return bool(_BOT_UA_PATTERN.search(ua))


# --- API endpoints for generating share links ---


@router.get("/api/share/books/{google_book_id}", response_model=ShareResponse)
async def share_book_endpoint(
    google_book_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a shareable link and OG metadata for a book."""
    book = await get_book_by_id(google_book_id, user_id=current_user.id)
    return share_book(
        db,
        google_book_id=book.google_book_id,
        title=book.title,
        authors=book.authors,
        thumbnail=book.thumbnail,
        description=book.description,
    )


@router.get("/api/share/lists/{list_id}", response_model=ShareResponse)
async def share_list_endpoint(
    list_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a shareable link and OG metadata for a book list."""
    repo = BookListRepository(db)
    book_list = repo.get_list(list_id)
    if not book_list:
        raise NotFoundError("Book list not found")
    if not book_list.is_public and book_list.user_id != current_user.id:
        raise NotFoundError("Book list not found")
    owner_username = book_list.user.email.split("@")[0]
    return share_list(db, book_list, owner_username)


@router.get("/api/share/users/{user_id}", response_model=ShareResponse)
async def share_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a shareable link and OG metadata for a user profile."""
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise NotFoundError("User not found")
    social_repo = SocialRepository(db)
    profile = social_repo.get_profile(user_id)
    return share_user(db, user, profile)


# --- Public OG meta pages (served to bots, redirect for humans) ---


@router.get("/books/{google_book_id}")
async def book_og_page(
    google_book_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Serve OG meta HTML to bots, redirect humans to the app."""
    if not _is_bot(request):
        return RedirectResponse(f"/book/{google_book_id}", status_code=302)
    try:
        book = await get_book_by_id(google_book_id)
        resp = share_book(
            db,
            google_book_id=book.google_book_id,
            title=book.title,
            authors=book.authors,
            thumbnail=book.thumbnail,
            description=book.description,
        )
        return HTMLResponse(render_og_html(resp.og))
    except Exception:
        return RedirectResponse(f"/book/{google_book_id}", status_code=302)


@router.get("/lists/{list_id}")
async def list_og_page(
    list_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Serve OG meta HTML to bots, redirect humans to the app."""
    if not _is_bot(request):
        return RedirectResponse(f"/social/lists/{list_id}", status_code=302)
    repo = BookListRepository(db)
    book_list = repo.get_list(list_id)
    if not book_list or not book_list.is_public:
        return RedirectResponse(f"/social/lists/{list_id}", status_code=302)
    owner_username = book_list.user.email.split("@")[0]
    resp = share_list(db, book_list, owner_username)
    return HTMLResponse(render_og_html(resp.og))


@router.get("/users/{user_id}")
async def user_og_page(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Serve OG meta HTML to bots, redirect humans to the app."""
    if not _is_bot(request):
        return RedirectResponse(f"/social/profile/{user_id}", status_code=302)
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        return RedirectResponse(f"/social/profile/{user_id}", status_code=302)
    social_repo = SocialRepository(db)
    profile = social_repo.get_profile(user_id)
    resp = share_user(db, user, profile)
    return HTMLResponse(render_og_html(resp.og))


# --- Short link resolution ---


@router.get("/s/{short_code}")
async def resolve_short_link(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Resolve a short link: serve OG HTML to bots, redirect humans."""
    link = resolve_short_code(db, short_code)
    if not link:
        raise NotFoundError("Short link not found")

    target_map = {
        "book": f"/books/{link.target_id}",
        "list": f"/lists/{link.target_id}",
        "user": f"/users/{link.target_id}",
    }
    target_path = target_map.get(link.target_type, "/")

    if _is_bot(request):
        # Redirect to the OG page which will render meta tags
        return RedirectResponse(target_path, status_code=302)

    # For humans, redirect to the app route
    app_map = {
        "book": f"/book/{link.target_id}",
        "list": f"/social/lists/{link.target_id}",
        "user": f"/social/profile/{link.target_id}",
    }
    return RedirectResponse(app_map.get(link.target_type, "/"), status_code=302)
