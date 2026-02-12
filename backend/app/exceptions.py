"""Custom exception classes for BookSwipe API.

All exceptions inherit from BookSwipeException and are caught by the global
exception handler middleware which returns structured JSON error responses.
"""


class BookSwipeException(Exception):
    """Base exception for all BookSwipe application errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: dict | list | str | None = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class AuthError(BookSwipeException):
    """Authentication or authorization failure."""

    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "AUTH_ERROR",
        details: dict | list | str | None = None,
    ):
        super().__init__(message=message, code=code, status_code=401, details=details)


class NotFoundError(BookSwipeException):
    """Requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        details: dict | list | str | None = None,
    ):
        super().__init__(message=message, code=code, status_code=404, details=details)


class ValidationError(BookSwipeException):
    """Request data failed validation."""

    def __init__(
        self,
        message: str = "Validation error",
        code: str = "VALIDATION_ERROR",
        details: dict | list | str | None = None,
    ):
        super().__init__(message=message, code=code, status_code=422, details=details)


class ConflictError(BookSwipeException):
    """Resource already exists or conflicts with current state."""

    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT",
        details: dict | list | str | None = None,
    ):
        super().__init__(message=message, code=code, status_code=409, details=details)


class RateLimitError(BookSwipeException):
    """Client has exceeded the allowed request rate."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Try again later.",
        code: str = "RATE_LIMIT_EXCEEDED",
        details: dict | list | str | None = None,
    ):
        super().__init__(message=message, code=code, status_code=429, details=details)


class ExternalAPIError(BookSwipeException):
    """An external service (e.g. Google Books) returned an error."""

    def __init__(
        self,
        message: str = "External service error",
        code: str = "EXTERNAL_API_ERROR",
        details: dict | list | str | None = None,
    ):
        super().__init__(message=message, code=code, status_code=502, details=details)
