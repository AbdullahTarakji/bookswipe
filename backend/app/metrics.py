"""Prometheus metrics: instrumentator setup and custom counters/gauges."""

from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

# Custom application metrics
active_users = Gauge(
    "bookswipe_active_users",
    "Number of currently active users (approximation)",
)

books_liked_total = Counter(
    "bookswipe_books_liked_total",
    "Total number of books liked",
)

books_skipped_total = Counter(
    "bookswipe_books_skipped_total",
    "Total number of books skipped",
)

auth_attempts_total = Counter(
    "bookswipe_auth_attempts_total",
    "Total authentication attempts",
    ["method", "status"],  # method: register/login/google/apple, status: success/failure
)


def create_instrumentator() -> Instrumentator:
    """Build a Prometheus instrumentator that exposes request metrics on /metrics."""
    return Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        excluded_handlers=["/metrics", "/health"],
        inprogress_name="bookswipe_http_requests_inprogress",
        inprogress_labels=True,
    )
