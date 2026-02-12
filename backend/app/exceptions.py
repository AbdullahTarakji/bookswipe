"""Custom exception hierarchy for the BookSwipe API.

All application-level exceptions inherit from BookSwipeException,
allowing a single global handler to convert them to structured JSON responses.
"""

from __future__ import annotations


class BookSwipeException(Exception):
    """Base exception for all BookSwipe application errors."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None, details: object = None) -> None:
        self.message = message or self.__class__.message
        self.details = details
        super().__init__(self.message)


class AuthError(BookSwipeException):
    """Raised for authentication and authorization failures."""

    status_code = 401
    code = "AUTH_ERROR"
    message = "Authentication failed"


class ForbiddenError(BookSwipeException):
    """Raised when the user lacks permission for the requested action."""

    status_code = 403
    code = "FORBIDDEN"
    message = "Insufficient permissions"


class NotFoundError(BookSwipeException):
    """Raised when a requested resource does not exist."""

    status_code = 404
    code = "NOT_FOUND"
    message = "Resource not found"


class ValidationError(BookSwipeException):
    """Raised when input validation fails at the application level."""

    status_code = 409
    code = "VALIDATION_ERROR"
    message = "Validation failed"


class ExternalAPIError(BookSwipeException):
    """Raised when an external API (e.g. Google Books) fails."""

    status_code = 502
    code = "EXTERNAL_API_ERROR"
    message = "External service unavailable"


class RateLimitError(BookSwipeException):
    """Raised when a per-user rate limit is exceeded."""

    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"
    message = "Rate limit exceeded. Try again later."


class SwipeLimitError(BookSwipeException):
    """Raised when a free-tier user exceeds their daily swipe limit."""

    status_code = 429
    code = "SWIPE_LIMIT_EXCEEDED"
    message = "Daily swipe limit reached. Upgrade to Premium for unlimited swipes."


class PaymentError(BookSwipeException):
    """Raised when a payment operation fails."""

    status_code = 400
    code = "PAYMENT_ERROR"
    message = "Payment operation failed"
