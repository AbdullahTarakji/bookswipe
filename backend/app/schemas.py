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
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    password_strength: dict | None = None


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


# --- Categories ---

class CategoryResponse(BaseModel):
    id: int
    name: str
    google_category_key: str

    model_config = {"from_attributes": True}


# --- Books ---

class BookSummary(BaseModel):
    google_book_id: str
    title: str
    authors: list[str]
    thumbnail: str
    categories: list[str] = []
    average_rating: float | None = None
    ratings_count: int | None = None


class BookDetail(BookSummary):
    description: str
    page_count: int | None = None
    published_date: str | None = None
    publisher: str | None = None
    preview_link: str | None = None
    info_link: str | None = None


class BookAction(BaseModel):
    google_book_id: str = Field(..., max_length=50)
    title: str = Field(default="", max_length=500)
    authors: str = Field(default="", max_length=500)
    thumbnail: str = Field(default="", max_length=500)

    @field_validator("title", "authors")
    @classmethod
    def sanitize_text(cls, v: str) -> str:
        return _sanitize_string(v)


class LikedBookResponse(BaseModel):
    id: int
    google_book_id: str
    title: str
    authors: str
    thumbnail: str
    liked_at: datetime.datetime

    model_config = {"from_attributes": True}


class PaginatedBooks(BaseModel):
    books: list[BookSummary]
    total: int
    page: int
    page_size: int


class PaginatedLikedBooks(BaseModel):
    books: list[LikedBookResponse]
    total: int
    page: int
    page_size: int


class MessageResponse(BaseModel):
    message: str
