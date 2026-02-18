"""Service for generating shareable deep links with OG metadata."""

from __future__ import annotations

import secrets
import html as html_mod

from sqlalchemy.orm import Session

from app.config import settings
from app.models import BookList, ShortLink, User, UserProfile
from app.schemas import OGMetadata, ShareResponse


def _get_or_create_short_code(db: Session, target_type: str, target_id: str) -> str:
    """Return an existing short code or create a new one."""
    link = (
        db.query(ShortLink)
        .filter(ShortLink.target_type == target_type, ShortLink.target_id == target_id)
        .first()
    )
    if link:
        return link.short_code
    code = secrets.token_urlsafe(6)  # ~8 chars
    db.add(ShortLink(short_code=code, target_type=target_type, target_id=target_id))
    db.commit()
    return code


def _base() -> str:
    return settings.app_base_url.rstrip("/")


def share_book(
    db: Session,
    google_book_id: str,
    title: str,
    authors: list[str],
    thumbnail: str | None,
    description: str = "",
) -> ShareResponse:
    """Generate a share response for a book."""
    url = f"{_base()}/books/{google_book_id}"
    short_code = _get_or_create_short_code(db, "book", google_book_id)
    authors_str = ", ".join(authors) if authors else "Unknown author"
    og_desc = description[:200] if description else f"A book by {authors_str}"

    return ShareResponse(
        url=url,
        short_url=f"{_base()}/s/{short_code}",
        og=OGMetadata(
            og_title=title,
            og_description=og_desc,
            og_image=thumbnail,
            og_type="book",
            og_url=url,
        ),
    )


def share_list(db: Session, book_list: BookList, owner_username: str) -> ShareResponse:
    """Generate a share response for a book list."""
    url = f"{_base()}/lists/{book_list.id}"
    short_code = _get_or_create_short_code(db, "list", str(book_list.id))
    item_count = len(book_list.items) if book_list.items else 0
    og_desc = book_list.description or f"A reading list with {item_count} books by {owner_username}"

    return ShareResponse(
        url=url,
        short_url=f"{_base()}/s/{short_code}",
        og=OGMetadata(
            og_title=book_list.name,
            og_description=og_desc[:200],
            og_type="website",
            og_url=url,
        ),
    )


def share_user(db: Session, user: User, profile: UserProfile | None) -> ShareResponse:
    """Generate a share response for a user profile."""
    username = user.email.split("@")[0]
    url = f"{_base()}/users/{user.id}"
    short_code = _get_or_create_short_code(db, "user", str(user.id))
    bio = (profile.bio if profile and profile.bio else f"{username}'s reading profile")

    return ShareResponse(
        url=url,
        short_url=f"{_base()}/s/{short_code}",
        og=OGMetadata(
            og_title=f"{username} on BookSwipe",
            og_description=bio[:200],
            og_image=profile.avatar_url if profile else None,
            og_type="profile",
            og_url=url,
        ),
    )


def resolve_short_code(db: Session, short_code: str) -> ShortLink | None:
    """Look up a short code and return the ShortLink if found."""
    return db.query(ShortLink).filter(ShortLink.short_code == short_code).first()


def render_og_html(og: OGMetadata) -> str:
    """Render an HTML page with OG meta tags for social media crawlers."""
    esc = html_mod.escape

    image_tag = ""
    if og.og_image:
        image_tag = f'<meta property="og:image" content="{esc(og.og_image)}" />'

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>{esc(og.og_title)}</title>
    <meta property="og:title" content="{esc(og.og_title)}" />
    <meta property="og:description" content="{esc(og.og_description)}" />
    <meta property="og:type" content="{esc(og.og_type)}" />
    <meta property="og:url" content="{esc(og.og_url)}" />
    {image_tag}
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{esc(og.og_title)}" />
    <meta name="twitter:description" content="{esc(og.og_description)}" />
</head>
<body>
    <p>Redirecting to BookSwipe...</p>
    <script>window.location.href = "{esc(og.og_url)}";</script>
</body>
</html>"""
