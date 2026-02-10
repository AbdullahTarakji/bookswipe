import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


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
    google_book_id: str
    title: str = ""
    authors: str = ""
    thumbnail: str = ""


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
