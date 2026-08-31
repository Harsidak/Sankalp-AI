"""
Middleware stack: CORS, request logging, rate limiting, global error handling.

All middleware is registered in main.py via setup_middleware().
"""

import time
import uuid
import logging
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.core.cache import get_cache
from app.core.exceptions import AppException

settings = get_settings()
logger = logging.getLogger("sankalp")


# =============================================================================
# Request Logging Middleware
# =============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with method, path, status code, and duration.
    Assigns a unique request ID for tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Attach request ID to state for downstream use
        request.state.request_id = request_id

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"→ {response.status_code} ({duration_ms:.1f}ms)"
        )

        response.headers["X-Request-ID"] = request_id
        return response


# =============================================================================
# Rate Limiting Middleware
# =============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket rate limiter per client IP.
    Uses the in-memory cache (swap to Redis for distributed deployments).

    Default: 100 requests per 60-second window.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.cache = get_cache()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path.endswith("/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        cache_key = f"rate_limit:{client_ip}"

        # Check current count
        current = await self.cache.get(cache_key)
        if current is not None and int(current) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                    },
                },
            )

        # Increment counter
        if current is None:
            await self.cache.set(cache_key, 1, ttl=self.window_seconds)
        else:
            await self.cache.incr(cache_key)

        response = await call_next(request)
        return response


# =============================================================================
# Global Error Handler Middleware
# =============================================================================

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Catches all unhandled exceptions and returns consistent JSON error responses.
    AppException subclasses are serialized with their specific status codes.
    Unknown exceptions become 500 Internal Server Error.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except AppException as exc:
            logger.warning(f"AppException: {exc.error_code} — {exc.message}")
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict(),
            )
        except Exception as exc:
            logger.exception(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "An unexpected error occurred",
                    },
                },
            )


# =============================================================================
# Middleware Registration
# =============================================================================

def setup_middleware(app: FastAPI) -> None:
    """Register all middleware on the FastAPI application."""

    # CORS — must be added first (outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Error handler — catches exceptions from all inner middleware and routes
    app.add_middleware(ErrorHandlerMiddleware)

    # Rate limiting
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

    # Request logging — innermost, logs after response is generated
    app.add_middleware(RequestLoggingMiddleware)
