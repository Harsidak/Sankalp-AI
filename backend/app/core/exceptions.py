"""
Custom exception hierarchy for consistent error handling.

All application exceptions inherit from AppException.
Each exception maps to an HTTP status code and a machine-readable error code.
The global error handler in middleware.py catches these and returns uniform responses.
"""

from typing import Any, Optional


class AppException(Exception):
    """Base exception for all application errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        self.message = message or self.__class__.message
        self.details = details
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Serialize to API error response format."""
        result = {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.message,
            },
        }
        if self.details:
            result["error"]["details"] = self.details
        return result


class AuthenticationError(AppException):
    """Raised when authentication fails (invalid credentials, expired token)."""
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"
    message = "Authentication failed"


class AuthorizationError(AppException):
    """Raised when user lacks permission for the requested action."""
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"
    message = "You do not have permission to perform this action"


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""
    status_code = 404
    error_code = "NOT_FOUND"
    message = "Resource not found"


class ConflictError(AppException):
    """Raised when a resource already exists (e.g., duplicate email)."""
    status_code = 409
    error_code = "CONFLICT"
    message = "Resource already exists"


class ValidationError(AppException):
    """Raised when input data fails validation."""
    status_code = 422
    error_code = "VALIDATION_ERROR"
    message = "Validation failed"


class RateLimitError(AppException):
    """Raised when a client exceeds the rate limit."""
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please try again later"


class AIServiceError(AppException):
    """Raised when the AI/LLM service fails."""
    status_code = 502
    error_code = "AI_SERVICE_ERROR"
    message = "AI service encountered an error"


class FileProcessingError(AppException):
    """Raised when file upload or processing fails."""
    status_code = 400
    error_code = "FILE_PROCESSING_ERROR"
    message = "Failed to process the uploaded file"
