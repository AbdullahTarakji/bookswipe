from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import SEED_CATEGORIES, Category

# Valid test password meeting all requirements
VALID_TEST_PASSWORD = "TestPass123"

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


@pytest.fixture(autouse=True)
def disable_rate_limiter():
    """Disable rate limiter during tests to avoid 429 errors."""
    from app.routers.auth import limiter as auth_limiter

    app_limiter = app.state.limiter
    app_limiter.enabled = False
    auth_limiter.enabled = False
    yield
    app_limiter.enabled = True
    auth_limiter.enabled = True


# In-memory store that simulates Redis during tests
_test_cache_store: dict[str, str] = {}
_test_blacklist_store: set[str] = set()


@pytest.fixture(autouse=True)
def mock_redis():
    """Mock all Redis cache operations with an in-memory store for tests."""
    import json

    _test_cache_store.clear()
    _test_blacklist_store.clear()

    async def _mock_cache_get(key):
        raw = _test_cache_store.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def _mock_cache_set(key, value, ttl=None):
        _test_cache_store[key] = json.dumps(value)

    async def _mock_cache_delete(key):
        _test_cache_store.pop(key, None)

    async def _mock_blacklist_add(jti, ttl):
        _test_blacklist_store.add(jti)

    async def _mock_blacklist_check(jti):
        return jti in _test_blacklist_store

    async def _mock_redis_ping():
        return True

    async def _mock_close_redis():
        pass

    with patch("app.services.cache.cache_get", side_effect=_mock_cache_get), \
         patch("app.services.cache.cache_set", side_effect=_mock_cache_set), \
         patch("app.services.cache.cache_delete", side_effect=_mock_cache_delete), \
         patch("app.services.cache.blacklist_add", side_effect=_mock_blacklist_add), \
         patch("app.services.cache.blacklist_check", side_effect=_mock_blacklist_check), \
         patch("app.services.cache.redis_ping", side_effect=_mock_redis_ping), \
         patch("app.services.cache.close_redis", side_effect=_mock_close_redis), \
         patch("app.services.google_books.cache_get", side_effect=_mock_cache_get), \
         patch("app.services.google_books.cache_set", side_effect=_mock_cache_set), \
         patch("app.services.auth.blacklist_add", side_effect=_mock_blacklist_add), \
         patch("app.services.auth.blacklist_check", side_effect=_mock_blacklist_check), \
         patch("app.main.redis_ping", side_effect=_mock_redis_ping), \
         patch("app.main.close_redis", side_effect=_mock_close_redis):
        yield


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
        "password": VALID_TEST_PASSWORD,
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
