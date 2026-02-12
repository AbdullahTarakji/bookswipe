"""Admin router: user management, analytics, and system info endpoints."""

import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    AdminUserResponse,
    AnalyticsResponse,
    BanUserRequest,
    MessageResponse,
    PaginatedAdminUsers,
    SystemInfoResponse,
    UpdateRoleRequest,
)
from app.services.admin import (
    ban_user,
    delete_user,
    get_analytics,
    get_system_info,
    get_user_by_id,
    get_users,
    require_admin,
    update_user_role,
)
from app.services.auth import get_current_user

logger = logging.getLogger("bookswipe")

router = APIRouter(prefix="/api/admin", tags=["admin"])


def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the current user is an admin."""
    return require_admin(current_user)


@router.get("/users", response_model=PaginatedAdminUsers)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = Query(None, max_length=255),
    role: str | None = Query(None, pattern=r"^(admin|user)$"),
    is_banned: bool | None = Query(None),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return a paginated list of users with optional search and filtering."""
    users, total = get_users(db, page, page_size, search, role, is_banned)
    return PaginatedAdminUsers(
        users=[AdminUserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return detailed information for a single user."""
    user = get_user_by_id(db, user_id)
    return AdminUserResponse.model_validate(user)


@router.put("/users/{user_id}/role", response_model=AdminUserResponse)
def change_user_role(
    user_id: int,
    body: UpdateRoleRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Update a user's role (admin or user)."""
    user = update_user_role(db, user_id, body.role, admin)
    return AdminUserResponse.model_validate(user)


@router.put("/users/{user_id}/ban", response_model=AdminUserResponse)
def toggle_ban_user(
    user_id: int,
    body: BanUserRequest = BanUserRequest(),
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Ban or unban a user. Toggles the current ban state."""
    user = ban_user(db, user_id, body.reason, admin)
    return AdminUserResponse.model_validate(user)


@router.delete("/users/{user_id}", response_model=MessageResponse)
def remove_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Permanently delete a user and all associated data."""
    delete_user(db, user_id, admin)
    return MessageResponse(message="User deleted")


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return analytics data for the admin dashboard."""
    data = get_analytics(db)
    return AnalyticsResponse(**data)


@router.get("/system", response_model=SystemInfoResponse)
def system_info(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Return system information including version, uptime, and resource usage."""
    return SystemInfoResponse(**get_system_info(db))
