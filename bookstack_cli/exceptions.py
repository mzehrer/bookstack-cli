"""Custom exceptions for BookStack API errors."""


class BookStackError(Exception):
    """Base exception for all BookStack API errors."""


class BookStackAuthError(BookStackError):
    """Authentication failed (401)."""


class BookStackNotFoundError(BookStackError):
    """Resource not found (404)."""


class BookStackRateLimitError(BookStackError):
    """Rate limit exceeded (429)."""


class BookStackServerError(BookStackError):
    """Server error (5xx)."""


class BookStackValidationError(BookStackError):
    """Validation error (422)."""


class BookStackConfigError(BookStackError):
    """Configuration error (missing URL or credentials)."""


STATUS_ERROR_MAP: dict[int, type[BookStackError]] = {
    401: BookStackAuthError,
    404: BookStackNotFoundError,
    422: BookStackValidationError,
    429: BookStackRateLimitError,
}


def map_status_to_error(status_code: int, message: str) -> BookStackError:
    """Map HTTP status code to appropriate exception."""
    exc_cls = STATUS_ERROR_MAP.get(status_code, BookStackError)
    if status_code >= 500:
        return BookStackServerError(message)
    return exc_cls(message)
