"""BookSwipe API application entry point.

Configures the FastAPI app with middleware, exception handlers, and route registration.
Integrates Prometheus metrics, structured JSON logging, and Sentry error tracking.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, SessionLocal, check_db_health
from app.exceptions import BookSwipeException
from app.logging_config import setup_logging
from app.metrics import create_instrumentator
from app.models import Category, User, SEED_CATEGORIES
from app.routers import admin, auth, books, categories, payments, recommendations
from app.services.auth import hash_password
from app.services.cache import close_redis, redis_ping
from app.sentry_setup import init_sentry

# Structured JSON logging
setup_logging()
logger = logging.getLogger("bookswipe")

# Track process start time for uptime calculation
_start_time = time.time()


def seed_categories(db: Session) -> None:
    """Populate the database with default book categories if empty."""
    existing = db.query(Category).count()
    if existing > 0:
        return
    for cat in SEED_CATEGORIES:
        db.add(Category(**cat))
    db.commit()


def seed_admin(db: Session) -> None:
    """Create a default admin user if no admin exists.

    Reads credentials from ADMIN_EMAIL / ADMIN_PASSWORD env vars.
    Skips seeding if either is unset so that production never creates an
    account with hardcoded credentials.
    """
    import os

    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_email or not admin_password:
        logger.debug("ADMIN_EMAIL/ADMIN_PASSWORD not set — skipping admin seed")
        return
    admin_exists = db.query(User).filter(User.role == "admin").first()
    if admin_exists:
        return
    admin_user = User(
        email=admin_email,
        hashed_password=hash_password(admin_password),
        role="admin",
        auth_provider="email",
    )
    db.add(admin_user)
    db.commit()
    logger.info("Admin user seeded: %s", admin_email)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown tasks."""
    # Initialize Sentry before anything else
    init_sentry()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_categories(db)
        seed_admin(db)
    finally:
        db.close()
    logger.info("BookSwipe API started (env=%s)", settings.environment)
    yield
    await close_redis()
    logger.info("BookSwipe API shutting down")


# Rate limiter with Redis storage for distributed rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.api_rate_limit],
    storage_uri=settings.redis_url,
    in_memory_fallback_enabled=True,
)

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

# Prometheus instrumentation
if settings.prometheus_enabled:
    instrumentator = create_instrumentator()
    instrumentator.instrument(app)
    instrumentator.expose(app, include_in_schema=False)


@app.exception_handler(BookSwipeException)
async def bookswipe_exception_handler(request: Request, exc: BookSwipeException) -> JSONResponse:
    """Global handler that converts BookSwipeException subclasses to structured JSON."""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "code=%s message=%s request_id=%s",
        exc.code,
        exc.message,
        request_id,
    )

    # Add context to Sentry if available
    try:
        import sentry_sdk
        sentry_sdk.set_context("request", {"request_id": request_id})
    except Exception:
        pass

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        },
    )


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Assign a unique request ID to each request and log request metrics."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()

    # Set Sentry context
    try:
        import sentry_sdk
        sentry_sdk.set_tag("request_id", request_id)
    except Exception:
        pass

    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "method=%s path=%s status=%d duration=%.1fms request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request_id,
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "duration_ms": round(duration_ms, 1),
            "status_code": response.status_code,
        },
    )
    return response


app.include_router(auth.router)
app.include_router(books.router)
app.include_router(categories.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(recommendations.router)


@app.get("/health")
async def health_check():
    """Return application health status with dependency checks."""
    uptime = round(time.time() - _start_time, 2)
    db_health = check_db_health()
    redis_ok = await redis_ping()

    db_status = db_health.get("status", "error") if isinstance(db_health, dict) else "ok"
    overall = "healthy" if db_status == "ok" else "unhealthy"

    return {
        "status": overall,
        "version": settings.app_version,
        "uptime": uptime,
        "dependencies": {
            "database": db_status,
            "redis": "connected" if redis_ok else "unavailable",
        },
    }


# Serve Flutter web frontend with SPA fallback (must be after all API routes)
import os as _os
import pathlib as _pathlib
_default_web = str(
    _pathlib.Path(__file__).resolve().parent.parent.parent / "frontend" / "build" / "web"
)
_flutter_web = _pathlib.Path(_os.environ.get("FLUTTER_WEB_DIR", _default_web))
if _flutter_web.exists():
    from starlette.staticfiles import StaticFiles
    from starlette.responses import FileResponse

    _flutter_static = StaticFiles(directory=str(_flutter_web))
    _index_html = str(_flutter_web / "index.html")

    @app.middleware("http")
    async def flutter_spa_fallback(request, call_next):
        response = await call_next(request)
        # If it's a 404 and not an API/health route, serve index.html (SPA fallback)
        if response.status_code == 404 and not request.url.path.startswith(("/api/", "/health")):
            return FileResponse(_index_html)
        return response

    app.mount("/", _flutter_static, name="flutter")
