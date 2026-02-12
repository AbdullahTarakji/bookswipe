"""BookSwipe FastAPI application entry point.

Configures middleware (CORS, security headers, request ID, exception handling),
structured JSON logging, rate limiting, and registers all routers.
"""

import logging
import time
import traceback
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pythonjsonlogger import jsonlogger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.exceptions import BookSwipeException
from app.models import SEED_CATEGORIES, Category
from app.routers import auth, books, categories

# --- Structured JSON logging ---

_SENSITIVE_FIELDS = frozenset(
    {"password", "secret_key", "access_token", "refresh_token", "authorization"}
)


class _RedactingFilter(logging.Filter):
    """Redact sensitive field values that appear in log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for field in _SENSITIVE_FIELDS:
            if field in msg.lower():
                record.msg = f"[REDACTED {field}]"
                record.args = None
        return True


def _setup_logging() -> logging.Logger:
    """Configure structured JSON logging for the application."""
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    handler.addFilter(_RedactingFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if settings.debug else logging.INFO)

    return logging.getLogger("bookswipe")


logger = _setup_logging()


# --- Lifespan ---


def seed_categories(db: Session) -> None:
    """Populate default book categories if the table is empty."""
    existing = db.query(Category).count()
    if existing > 0:
        return
    for cat in SEED_CATEGORIES:
        db.add(Category(**cat))
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed data on startup; log shutdown."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_categories(db)
    finally:
        db.close()
    logger.info("BookSwipe API started", extra={"environment": settings.environment})
    yield
    logger.info("BookSwipe API shutting down")


# --- App & rate limiter ---

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.api_rate_limit])

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# --- Global exception handlers ---


@app.exception_handler(BookSwipeException)
async def bookswipe_exception_handler(request: Request, exc: BookSwipeException):
    """Convert custom exceptions to structured JSON error responses."""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "Application error: %s",
        exc.message,
        extra={
            "error_code": exc.code,
            "status_code": exc.status_code,
            "request_id": request_id,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
        headers={"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else {},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic validation errors to structured JSON."""
    details = []
    for err in exc.errors():
        details.append({
            "field": ".".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", ""),
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": details,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected exceptions — log full traceback, return 500."""
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "Unhandled exception: %s",
        str(exc),
        extra={
            "request_id": request_id,
            "traceback": traceback.format_exc(),
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": None,
            }
        },
    )


# --- Middleware ---


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to every response."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Generate a unique request ID per request, include in response and logs."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "HTTP request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 1),
            "request_id": request_id,
        },
    )
    return response


# --- Routers ---

app.include_router(auth.router)
app.include_router(books.router)
app.include_router(categories.router)


@app.get("/health")
def health_check():
    """Return API health status, version, and environment."""
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
    }
