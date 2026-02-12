"""Admin service: business logic for admin operations."""

from __future__ import annotations

import datetime
import os
import platform
import resource
import sys
import time

from sqlalchemy.orm import Session

from app.config import settings
from app.database import check_db_health
from app.exceptions import AuthError, NotFoundError, ValidationError
from app.models import User
from app.repositories.admin_repository import AdminRepository
from app.services.auth import get_current_user, hash_password


# Track process start time
_process_start_time = time.time()


def require_admin(user: User) -> User:
    """Verify the user has the admin role. Raises AuthError if not."""
    if user.role != "admin":
        raise AuthError("Admin access required")
    return user


def get_users(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    role: str | None = None,
    is_banned: bool | None = None,
) -> tuple[list[User], int]:
    """Return paginated, filtered users."""
    repo = AdminRepository(db)
    return repo.get_users(page, page_size, search, role, is_banned)


def get_user_by_id(db: Session, user_id: int) -> User:
    """Return a user by ID or raise NotFoundError."""
    repo = AdminRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


def update_user_role(db: Session, user_id: int, new_role: str, current_admin: User) -> User:
    """Update a user's role."""
    if new_role not in ("admin", "user"):
        raise ValidationError("Role must be 'admin' or 'user'")
    if user_id == current_admin.id:
        raise ValidationError("Cannot change your own role")

    repo = AdminRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    return repo.update_role(user, new_role)


def ban_user(db: Session, user_id: int, reason: str | None, current_admin: User) -> User:
    """Ban or unban a user."""
    repo = AdminRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    if user.id == current_admin.id:
        raise ValidationError("Cannot ban yourself")
    if user.role == "admin":
        raise ValidationError("Cannot ban an admin user")
    if user.is_banned:
        return repo.unban_user(user)
    return repo.ban_user(user, reason)


def delete_user(db: Session, user_id: int, current_admin: User) -> None:
    """Hard-delete a user."""
    repo = AdminRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    if user.id == current_admin.id:
        raise ValidationError("Cannot delete yourself")
    if user.role == "admin":
        raise ValidationError("Cannot delete an admin user")
    repo.hard_delete_user(user)


def get_analytics(db: Session) -> dict:
    """Gather analytics data for the admin dashboard."""
    repo = AdminRepository(db)
    now = datetime.datetime.now(datetime.timezone.utc)
    seven_days_ago = now - datetime.timedelta(days=7)

    return {
        "total_users": repo.get_total_users(),
        "active_users_7d": repo.get_active_users(seven_days_ago),
        "banned_users": repo.get_banned_users_count(),
        "admin_users": repo.get_admin_users_count(),
        "total_likes": repo.get_total_likes(),
        "total_skips": repo.get_total_skips(),
        "user_growth": repo.get_user_growth(30),
        "popular_categories": repo.get_popular_categories(10),
        "recent_users": [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "is_banned": u.is_banned,
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in repo.get_recent_users(5)
        ],
    }


def get_system_info(db: Session) -> dict:
    """Return comprehensive system information."""
    db_health = check_db_health()
    uptime_seconds = time.time() - _process_start_time

    # Memory usage
    try:
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        memory_mb = rusage.ru_maxrss / (1024 * 1024) if sys.platform == "linux" else rusage.ru_maxrss / (1024 * 1024)
    except Exception:
        memory_mb = 0

    return {
        "app_version": settings.app_version,
        "environment": settings.environment,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "uptime_seconds": round(uptime_seconds, 2),
        "uptime_human": _format_uptime(uptime_seconds),
        "database": db_health,
        "redis": {
            "url_configured": bool(settings.redis_url),
        },
        "memory_usage_mb": round(memory_mb, 2),
        "pid": os.getpid(),
    }


def _format_uptime(seconds: float) -> str:
    """Format seconds to a human-readable uptime string."""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
