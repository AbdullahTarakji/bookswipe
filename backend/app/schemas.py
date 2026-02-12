"""Pydantic request/response schemas for the BookSwipe API."""

import datetime
import re

from pydantic import BaseModel, EmailStr, Field, field_validator

# Common passwords (top subset for validation)
COMMON_PASSWORDS = frozenset([
    "password", "12345678", "123456789", "1234567890", "qwerty123",
    "password1", "password123", "iloveyou", "sunshine1", "princess1",
    "football1", "charlie1", "shadow12", "michael1", "qwerty12",
    "abc12345", "abcdefgh", "trustno1", "letmein1", "dragon12",
    "master12", "monkey12", "baseball1", "mustang1", "access14",
    "starwars1", "passw0rd", "p@ssw0rd", "p@ssword", "welcome1",
    "qwertyui", "asdfghjk", "zxcvbnm1", "admin123", "login123",
    "changeme", "test1234", "pass1234", "user1234", "root1234",
])


def _sanitize_string(value: str) -> str:
    """Strip HTML/script tags from string input."""
    value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", "", value)
    return value.strip()


def check_password_strength(password: str) -> dict:
    """Evaluate password strength and return feedback."""
    score = 0
    feedback = []

    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Add an uppercase letter")
    if re.search(r"[a-z]", password):
        score += 1
    else:
        feedback.append("Add a lowercase letter")
    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Add a number")
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1

    if score <= 2:
        strength = "weak"
    elif score <= 4:
        strength = "moderate"
    else:
        strength = "strong"

    return {"strength": strength, "score": score, "feedback": feedback}


# --- Auth ---

class UserRegister(BaseModel):
    """Request schema for user registration with email and password."""
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if v.lower() in COMMON_PASSWORDS:
            raise ValueError("This password is too common. Please choose a more unique password")
        return v

    @field_validator("email")
    @classmethod
    def validate_email_strict(cls, v: str) -> str:
        local, _, domain = v.partition("@")
        if not domain or "." not in domain:
            raise ValueError("Invalid email domain")
        if len(local) > 64:
            raise ValueError("Email local part too long")
        return v.lower().strip()


class UserLogin(BaseModel):
    """Request schema for user login with email and password."""
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class TokenResponse(BaseModel):
    """Response schema containing access and refresh JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    password_strength: dict | None = None


class TokenRefresh(BaseModel):
    """Request schema for token refresh."""
    refresh_token: str


class UserResponse(BaseModel):
    """Response schema for user profile information."""
    id: int
    email: str
    role: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- Categories ---

class CategoryResponse(BaseModel):
    """Response schema for a book category."""
    id: int
    name: str
    google_category_key: str

    model_config = {"from_attributes": True}


# --- Books ---

class BookSummary(BaseModel):
    """Summary of a book used in discovery listings."""
    google_book_id: str
    title: str
    authors: list[str]
    thumbnail: str
    categories: list[str] = []
    average_rating: float | None = None
    ratings_count: int | None = None


class BookDetail(BookSummary):
    """Full book details including description and metadata."""
    description: str
    page_count: int | None = None
    published_date: str | None = None
    publisher: str | None = None
    preview_link: str | None = None
    info_link: str | None = None


class BookAction(BaseModel):
    """Request schema for liking or skipping a book."""
    google_book_id: str = Field(..., max_length=50)
    title: str = Field(default="", max_length=500)
    authors: str = Field(default="", max_length=500)
    thumbnail: str = Field(default="", max_length=500)

    @field_validator("title", "authors")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        return _sanitize_string(v)


class LikedBookResponse(BaseModel):
    """Response schema for a liked book record."""
    id: int
    google_book_id: str
    title: str
    authors: str
    thumbnail: str
    liked_at: datetime.datetime

    model_config = {"from_attributes": True}


class PaginatedBooks(BaseModel):
    """Paginated response containing book summaries."""
    books: list[BookSummary]
    total: int
    page: int
    page_size: int


class PaginatedLikedBooks(BaseModel):
    """Paginated response containing liked book records."""
    books: list[LikedBookResponse]
    total: int
    page: int
    page_size: int


class GoogleAuthRequest(BaseModel):
    """Request schema for Google OAuth sign-in."""
    id_token: str


class AppleAuthRequest(BaseModel):
    """Request schema for Apple OAuth sign-in."""
    authorization_code: str
    identity_token: str


class MessageResponse(BaseModel):
    """Generic response schema containing a status message."""
    message: str


# --- Admin ---

class AdminUserResponse(BaseModel):
    """Response schema for admin user listing."""
    id: int
    email: str
    role: str
    is_active: bool
    is_banned: bool
    banned_at: datetime.datetime | None = None
    ban_reason: str | None = None
    auth_provider: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class PaginatedAdminUsers(BaseModel):
    """Paginated response for admin user listing."""
    users: list[AdminUserResponse]
    total: int
    page: int
    page_size: int


class UpdateRoleRequest(BaseModel):
    """Request schema for updating a user's role."""
    role: str = Field(..., pattern=r"^(admin|user)$")


class BanUserRequest(BaseModel):
    """Request schema for banning a user."""
    reason: str | None = Field(None, max_length=500)


class AnalyticsResponse(BaseModel):
    """Response schema for admin analytics dashboard."""
    total_users: int
    active_users_7d: int
    banned_users: int
    admin_users: int
    total_likes: int
    total_skips: int
    user_growth: list[dict]
    popular_categories: list[dict]
    recent_users: list[dict]


class SystemInfoResponse(BaseModel):
    """Response schema for system information."""
    app_version: str
    environment: str
    python_version: str
    platform: str
    uptime_seconds: float
    uptime_human: str
    database: dict
    redis: dict
    memory_usage_mb: float
    pid: int
