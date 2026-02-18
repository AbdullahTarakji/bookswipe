"""Pydantic request/response schemas for the BookSwipe API."""

import datetime
import enum
import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class PlatformType(str, enum.Enum):
    """Client platform for routing to the correct billing provider."""
    WEB = "web"
    IOS = "ios"
    ANDROID = "android"

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
    subscription_status: str = "free"
    subscription_plan: str = "free"
    subscription_end_date: datetime.datetime | None = None

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
    description: str = ""
    page_count: int | None = None
    published_date: str | None = None
    publisher: str | None = None
    blurhash: str | None = None
    thumbnail_cdn: str | None = None
    card_cdn: str | None = None
    detail_cdn: str | None = None


class BookDetail(BookSummary):
    """Full book details including description and metadata."""
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


# --- Payments / Subscriptions ---

class SubscriptionResponse(BaseModel):
    """Response schema for subscription status."""
    subscription_status: str
    subscription_plan: str
    subscription_end_date: datetime.datetime | None = None
    is_premium: bool = False

    model_config = {"from_attributes": True}


class CheckoutSessionResponse(BaseModel):
    """Response schema for a Stripe checkout session."""
    checkout_url: str


class SwipeLimitResponse(BaseModel):
    """Response schema for swipe limit status."""
    swipes_today: int
    daily_limit: int
    is_premium: bool
    swipes_remaining: int


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


# --- Recommendations ---

class SwipeEventCreate(BaseModel):
    """Request schema for recording a swipe event with metadata."""

    google_book_id: str = Field(..., max_length=50)
    action: str = Field(..., pattern=r"^(like|skip|superlike)$")
    genre: str = Field(default="", max_length=200)
    author: str = Field(default="", max_length=500)
    category: str = Field(default="", max_length=200)

    @field_validator("genre", "author", "category")
    @classmethod
    def sanitize_metadata(cls, v: str) -> str:
        """Strip HTML tags from metadata fields."""
        return _sanitize_string(v)


class SwipeEventResponse(BaseModel):
    """Response schema for a recorded swipe event."""

    id: int
    google_book_id: str
    action: str
    genre: str
    author: str
    category: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class UserPreferenceResponse(BaseModel):
    """Response schema for computed user preferences."""

    genre_scores: dict[str, float]
    author_scores: dict[str, float]
    category_scores: dict[str, float]
    updated_at: datetime.datetime | None = None


class PaginatedRecommendations(BaseModel):
    """Paginated response containing recommended book summaries."""

    books: list[BookSummary]
    total: int
    page: int
    page_size: int


# --- Notifications ---


class DeviceTokenRegister(BaseModel):
    """Request schema for registering an FCM device token."""

    token: str = Field(..., min_length=1, max_length=500)
    platform: str = Field(default="android", pattern=r"^(android|ios|web)$")


class DeviceTokenUnregister(BaseModel):
    """Request schema for removing an FCM device token."""

    token: str = Field(..., min_length=1, max_length=500)


class NotificationPreferenceResponse(BaseModel):
    """Response schema for notification preferences."""

    recommendations: bool = True
    social: bool = True
    marketing: bool = False

    model_config = {"from_attributes": True}


class NotificationPreferenceUpdate(BaseModel):
    """Request schema for updating notification preferences."""

    recommendations: bool | None = None
    social: bool | None = None
    marketing: bool | None = None


class EmailPreferenceResponse(BaseModel):
    """Response schema for email notification preferences."""

    email_welcome: bool = True
    email_weekly_digest: bool = True
    email_recommendations: bool = True

    model_config = {"from_attributes": True}


class EmailPreferenceUpdate(BaseModel):
    """Request schema for updating email notification preferences."""

    email_welcome: bool | None = None
    email_weekly_digest: bool | None = None
    email_recommendations: bool | None = None


class NotificationResponse(BaseModel):
    """Response schema for a single notification."""

    id: int
    title: str
    body: str
    category: str
    deep_link: str | None = None
    is_read: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class PaginatedNotifications(BaseModel):
    """Paginated response containing notification records."""

    notifications: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    unread_count: int


# --- Social / Profiles ---


class UserProfileResponse(BaseModel):
    """Response schema for a user profile."""

    user_id: int
    username: str
    bio: str = ""
    avatar_url: str | None = None
    is_public: bool = True
    reading_goal: int | None = None
    followers_count: int = 0
    following_count: int = 0
    books_liked_count: int = 0
    is_following: bool = False


class UserProfileUpdate(BaseModel):
    """Request schema for updating a user profile."""

    bio: str | None = Field(None, max_length=500)
    avatar_url: str | None = Field(None, max_length=500)
    is_public: bool | None = None
    reading_goal: int | None = Field(None, ge=1, le=1000)

    @field_validator("bio")
    @classmethod
    def sanitize_bio(cls, v: str | None) -> str | None:
        if v is not None:
            return _sanitize_string(v)
        return v


class FollowResponse(BaseModel):
    """Response schema for a follow relationship."""

    user_id: int
    username: str
    avatar_url: str | None = None
    is_following: bool = False


class PaginatedFollows(BaseModel):
    """Paginated response containing follow relationships."""

    users: list[FollowResponse]
    total: int
    page: int
    page_size: int


class BookListCreate(BaseModel):
    """Request schema for creating a book list."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    is_public: bool = True

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: str) -> str:
        return _sanitize_string(v)


class BookListUpdate(BaseModel):
    """Request schema for updating a book list."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    is_public: bool | None = None

    @field_validator("name", "description")
    @classmethod
    def sanitize_text_fields(cls, v: str | None) -> str | None:
        if v is not None:
            return _sanitize_string(v)
        return v


class BookListItemAdd(BaseModel):
    """Request schema for adding a book to a list."""

    book_id: str = Field(..., max_length=50)
    note: str = Field(default="", max_length=500)

    @field_validator("note")
    @classmethod
    def sanitize_note(cls, v: str) -> str:
        return _sanitize_string(v)


class BookListItemResponse(BaseModel):
    """Response schema for a book list item."""

    id: int
    book_id: str
    note: str = ""
    added_at: datetime.datetime

    model_config = {"from_attributes": True}


class BookListResponse(BaseModel):
    """Response schema for a book list."""

    id: int
    user_id: int
    name: str
    description: str = ""
    is_public: bool = True
    created_at: datetime.datetime
    item_count: int = 0
    owner_username: str = ""

    model_config = {"from_attributes": True}


class BookListDetailResponse(BookListResponse):
    """Response schema for a book list with its items."""

    items: list[BookListItemResponse] = []


class PaginatedBookLists(BaseModel):
    """Paginated response containing book lists."""

    lists: list[BookListResponse]
    total: int
    page: int
    page_size: int


class ActivityEventResponse(BaseModel):
    """Response schema for an activity event."""

    id: int
    user_id: int
    username: str = ""
    event_type: str
    metadata: dict = {}
    created_at: datetime.datetime


class PaginatedActivityFeed(BaseModel):
    """Paginated response for the activity feed."""

    events: list[ActivityEventResponse]
    total: int
    page: int
    page_size: int


class UserSearchResponse(BaseModel):
    """Response schema for user search results."""

    users: list[FollowResponse]
    total: int


# --- Reviews & Ratings ---


class ReviewCreate(BaseModel):
    """Request schema for creating/updating a book review."""

    rating: int = Field(..., ge=1, le=5)
    review_text: str = Field("", max_length=5000)

    @field_validator("review_text")
    @classmethod
    def sanitize_review_text(cls, v: str) -> str:
        return _sanitize_string(v)


class ReviewUpdate(BaseModel):
    """Request schema for updating a book review."""

    rating: int | None = Field(None, ge=1, le=5)
    review_text: str | None = Field(None, max_length=5000)

    @field_validator("review_text")
    @classmethod
    def sanitize_review_text(cls, v: str | None) -> str | None:
        if v is not None:
            return _sanitize_string(v)
        return v


class ReviewResponse(BaseModel):
    """Response schema for a book review."""

    id: int
    user_id: int
    username: str = ""
    google_book_id: str
    rating: int
    review_text: str
    is_flagged: bool = False
    helpful_count: int = 0
    user_has_voted: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime


class PaginatedReviews(BaseModel):
    """Paginated response for book reviews."""

    reviews: list[ReviewResponse]
    total: int
    page: int
    page_size: int
    average_rating: float | None = None
    total_ratings: int = 0


class ReviewFlagRequest(BaseModel):
    """Admin request to flag a review."""

    reason: str = Field(..., min_length=1, max_length=500)


# --- Search Feature Schemas ---


class SearchFilters(BaseModel):
    """Filters for book search."""
    category: str | None = None
    author: str | None = None
    min_rating: float | None = None
    year_from: int | None = None
    year_to: int | None = None


class BookSearchResult(BaseModel):
    google_book_id: str
    title: str
    authors: list[str] = []
    thumbnail: str = ""
    categories: list[str] = []
    average_rating: float | None = None
    published_date: str | None = None


class UserSearchResult(BaseModel):
    user_id: int
    username: str
    avatar_url: str | None = None
    bio: str = ""
    is_following: bool = False


class ListSearchResult(BaseModel):
    id: int
    name: str
    description: str = ""
    user_id: int
    username: str = ""
    item_count: int = 0
    is_public: bool = True


class UnifiedSearchResponse(BaseModel):
    books: list[BookSearchResult] = []
    users: list[UserSearchResult] = []
    lists: list[ListSearchResult] = []
    total_books: int = 0
    total_users: int = 0
    total_lists: int = 0


class SearchHistoryItem(BaseModel):
    id: int
    query: str
    search_type: str = "all"
    created_at: datetime.datetime
    model_config = {"from_attributes": True}


class SearchHistoryResponse(BaseModel):
    items: list[SearchHistoryItem]
    total: int


class AutocompleteResponse(BaseModel):
    suggestions: list[str]


class TrendingSearch(BaseModel):
    query: str
    count: int


class TrendingSearchesResponse(BaseModel):
    searches: list[TrendingSearch]


# ── Share ────────────────────────────────────────────────────

class OGMetadata(BaseModel):
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_type: str = ""
    og_url: str = ""


class ShareResponse(BaseModel):
    url: str
    short_url: str
    og: OGMetadata = OGMetadata()


# ── Social (additional) ─────────────────────────────────────

class BookListReorder(BaseModel):
    item_ids: list[int]


# ── Analytics (admin) ────────────────────────────────────────

class CategoryCount(BaseModel):
    category: str
    count: int


class CategoryBreakdown(BaseModel):
    likes_by_category: list[CategoryCount] = []
    most_active_categories: list[CategoryCount] = []


class SwipeStats(BaseModel):
    total_swipes: int = 0
    likes: int = 0
    skips: int = 0
    like_rate: float = 0.0


class PopularBooks(BaseModel):
    most_liked: list[dict] = []
    most_swiped: list[dict] = []


class EngagementMetrics(BaseModel):
    total_users: int = 0
    active_users_today: int = 0
    active_users_week: int = 0
    avg_swipes_per_user: float = 0.0


class RetentionData(BaseModel):
    daily: list[dict] = []
    weekly: list[dict] = []


class DetailedAnalyticsResponse(BaseModel):
    engagement: EngagementMetrics = EngagementMetrics()
    swipes: SwipeStats = SwipeStats()
    popular_books: PopularBooks = PopularBooks()
    retention: RetentionData = RetentionData()
    categories: CategoryBreakdown = CategoryBreakdown()


# ── Privacy / Compliance ─────────────────────────────────────

class PrivacyConsentUpdate(BaseModel):
    """Request schema for updating privacy consent preferences."""
    analytics_consent: bool = False
    marketing_consent: bool = False


class PrivacyConsentResponse(BaseModel):
    """Response schema for privacy consent status."""
    analytics_consent: bool
    marketing_consent: bool
    consent_date: str | None = None
