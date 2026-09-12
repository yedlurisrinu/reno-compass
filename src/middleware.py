"""Application middleware for structured telemetry logging and API rate-limiting."""

import json
import logging
import time
import uuid
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from config.config import settings

# Setup structured logger
logger = logging.getLogger("reno_project")


class TokenBucketLimiter:
    """Standard token-bucket rate limiter implementing sliding refill."""

    def __init__(self, refill_rate_per_min: int, capacity: int):
        self.refill_rate = refill_rate_per_min
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.last_refill = time.time()

    def allow_request(self) -> bool:
        """Determines if a request passes rate-limiting checks, refilling tokens."""
        now = time.time()
        elapsed = now - self.last_refill
        # Refill rate is tokens-per-second: refill_rate / 60.0
        refill_amount = elapsed * (self.refill_rate / 60.0)
        self.tokens = min(self.capacity, self.tokens + refill_amount)
        self.last_refill = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


# Global in-memory registry of limiters keyed by client IP or session token
LIMITERS: dict[str, TokenBucketLimiter] = {}


def is_rate_limited(client_key: str) -> bool:
    """Verifies if the client has exceeded request limits.

    Args:
        client_key: Unique identifier (IP or token).

    Returns:
        bool: True if rate limit is breached.
    """
    if client_key not in LIMITERS:
        LIMITERS[client_key] = TokenBucketLimiter(
            settings.rate_limit_per_minute, settings.rate_limit_burst
        )
    return not LIMITERS[client_key].allow_request()


class TelemetryLoggingMiddleware(BaseHTTPMiddleware):
    """Observability middleware injecting correlation IDs and logging execution details.

    Excludes sensitive inputs/responses to protect user privacy (Dimension 10).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id

        start_time = time.time()

        # Check API Rate Limiting on chat endpoints (1 request/min)
        if request.url.path == "/api/chat" and request.method == "POST":
            # Identify client by IP address or cookie
            client_ip = request.client.host if request.client else "unknown"
            session_cookie = request.cookies.get("reno_session_token", client_ip)

            if is_rate_limited(session_cookie):
                log_payload = {
                    "correlation_id": correlation_id,
                    "event": "RATE_LIMIT_EXCEEDED",
                    "client": session_cookie,
                    "path": request.url.path,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
                logger.warning(json.dumps(log_payload))
                return JSONResponse(
                    status_code=429,
                    content={
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Rate limit is capped at 1 chat request per minute.",
                        "details": None,
                        "detail": "Too many requests. Rate limit is capped at 1 chat request per minute.",
                    },
                )

        try:
            response = await call_next(request)
        except Exception as exc:
            # Observability: Log unhandled exceptions
            duration = time.time() - start_time
            log_payload = {
                "correlation_id": correlation_id,
                "event": "UNHANDLED_EXCEPTION",
                "method": request.method,
                "path": request.url.path,
                "error": str(exc),
                "duration_seconds": round(duration, 4),
            }
            logger.error(json.dumps(log_payload))
            return JSONResponse(
                status_code=500,
                content={
                    "error_code": "GENERIC_INTERNAL_ERROR",
                    "message": "An unexpected error occurred on the server.",
                    "details": str(exc),
                    "detail": "An unexpected error occurred on the server.",
                },
            )

        duration = time.time() - start_time

        # Telemetry payload
        log_payload = {
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_seconds": round(duration, 4),
        }

        logger.info(json.dumps(log_payload))
        response.headers["X-Correlation-ID"] = correlation_id

        # Prevent browser caching of static files and root page
        if request.url.path == "/" or request.url.path.startswith("/static"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response
