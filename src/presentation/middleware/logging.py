"""Request logging middleware."""

import time
import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)
DEBUG_LOG_PATH = Path("/Users/daribazar/Documents/diplom/.cursor/debug-e5243e.log")


def _debug_log(location: str, message: str, data: dict) -> None:
    # region agent log
    try:
        payload = {
            "sessionId": "e5243e",
            "runId": "post-fix",
            "hypothesisId": "H6",
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(datetime.now(tz=timezone.utc).timestamp() * 1000),
        }
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        pass
    # endregion


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests."""

    async def dispatch(self, request: Request, call_next):
        """Log request and response."""
        start_time = time.time()

        logger.info(f"Request: {request.method} {request.url.path}")
        _debug_log(
            "src/presentation/middleware/logging.py:40",
            "Request received by LoggingMiddleware",
            {"method": request.method, "path": request.url.path},
        )

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} - " f"Completed in {process_time:.3f}s"
        )
        _debug_log(
            "src/presentation/middleware/logging.py:52",
            "Response handled by LoggingMiddleware",
            {"path": request.url.path, "status_code": response.status_code},
        )

        return response
