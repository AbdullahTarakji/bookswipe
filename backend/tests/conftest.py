from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import SEED_CATEGORIES, Category

TEST_DB_URL = "sqlite:///./test_bookswipe.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    if db.query(Category).count() == 0:
        for cat in SEED_CATEGORIES:
            db.add(Category(**cat))
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def registered_user(client):
    resp = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
    })
    return resp.json()


@pytest.fixture()
def auth_headers(registered_user):
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


MOCK_GOOGLE_BOOKS_SEARCH_RESPONSE = {
    "totalItems": 2,
    "items": [
        {
            "id": "book_1",
            "volumeInfo": {
                "title": "Test Book One",
                "authors": ["Author A"],
                "description": "A test book description.",
                "pageCount": 200,
                "categories": ["Fiction"],
                "imageLinks": {"thumbnail": "https://books.google.com/thumb1.jpg"},
                "averageRating": 4.0,
                "ratingsCount": 100,
                "publishedDate": "2023-01-01",
                "publisher": "Test Publisher",
                "previewLink": "https://books.google.com/preview1",
                "infoLink": "https://books.google.com/info1",
            },
        },
        {
            "id": "book_2",
            "volumeInfo": {
                "title": "Test Book Two",
                "authors": ["Author B", "Author C"],
                "description": "Another test book.",
                "pageCount": 350,
                "categories": ["Fiction"],
                "imageLinks": {"thumbnail": "https://books.google.com/thumb2.jpg"},
                "averageRating": 3.5,
                "ratingsCount": 50,
            },
        },
    ],
}

MOCK_GOOGLE_BOOK_DETAIL_RESPONSE = {
    "id": "book_1",
    "volumeInfo": {
        "title": "Test Book One",
        "authors": ["Author A"],
        "description": "A test book description.",
        "pageCount": 200,
        "categories": ["Fiction"],
        "imageLinks": {"thumbnail": "https://books.google.com/thumb1.jpg"},
        "averageRating": 4.0,
        "ratingsCount": 100,
        "publishedDate": "2023-01-01",
        "publisher": "Test Publisher",
        "previewLink": "https://books.google.com/preview1",
        "infoLink": "https://books.google.com/info1",
    },
}


@pytest.fixture(autouse=True)
def clear_google_books_cache():
    from app.services.google_books import clear_cache
    clear_cache()
    yield
    clear_cache()


@pytest.fixture()
def mock_google_books_search():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_GOOGLE_BOOKS_SEARCH_RESPONSE

    with patch("app.services.google_books.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client
        yield mock_client


@pytest.fixture()
def mock_google_book_detail():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_GOOGLE_BOOK_DETAIL_RESPONSE

    with patch("app.services.google_books.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client
        yield mock_client
