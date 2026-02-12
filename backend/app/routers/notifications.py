"""Notification router: device registration, preferences, and notification history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas import (
    DeviceTokenRegister,
    DeviceTokenUnregister,
    MessageResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    PaginatedNotifications,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post("/register-device", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    body: DeviceTokenRegister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Store an FCM device token for push notification delivery."""
    repo = NotificationRepository(db)
    repo.register_device_token(current_user.id, body.token, body.platform)
    return MessageResponse(message="Device registered successfully")


@router.post("/unregister-device", response_model=MessageResponse)
def unregister_device(
    body: DeviceTokenUnregister,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Remove an FCM device token."""
    repo = NotificationRepository(db)
    repo.unregister_device_token(current_user.id, body.token)
    return MessageResponse(message="Device unregistered successfully")


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPreferenceResponse:
    """Return the current user's notification preferences."""
    repo = NotificationRepository(db)
    prefs = repo.get_preferences(current_user.id)
    if prefs is None:
        return NotificationPreferenceResponse()
    return NotificationPreferenceResponse.model_validate(prefs)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    body: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPreferenceResponse:
    """Update the current user's notification preferences."""
    repo = NotificationRepository(db)
    prefs = repo.upsert_preferences(
        current_user.id,
        recommendations=body.recommendations,
        social=body.social,
        marketing=body.marketing,
    )
    return NotificationPreferenceResponse.model_validate(prefs)


@router.get("/history", response_model=PaginatedNotifications)
def notification_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedNotifications:
    """Return the current user's notification history with pagination."""
    repo = NotificationRepository(db)
    notifications, total = repo.get_notifications(current_user.id, page=page, page_size=page_size)
    unread_count = repo.get_unread_count(current_user.id)
    return PaginatedNotifications(
        notifications=notifications,
        total=total,
        page=page,
        page_size=page_size,
        unread_count=unread_count,
    )


@router.post("/history/{notification_id}/read", response_model=MessageResponse)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Mark a single notification as read."""
    repo = NotificationRepository(db)
    repo.mark_as_read(current_user.id, notification_id)
    return MessageResponse(message="Notification marked as read")


@router.post("/history/read-all", response_model=MessageResponse)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    """Mark all notifications as read for the current user."""
    repo = NotificationRepository(db)
    count = repo.mark_all_as_read(current_user.id)
    return MessageResponse(message=f"{count} notifications marked as read")
