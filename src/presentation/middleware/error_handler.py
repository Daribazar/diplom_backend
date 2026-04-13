"""Global error handling middleware."""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.core.exceptions import AppException
import logging
import json
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
DEBUG_LOG_PATH = Path("/Users/daribazar/Documents/diplom/.cursor/debug-e5243e.log")


def _debug_log(location: str, message: str, data: dict) -> None:
    # region agent log
    try:
        payload = {
            "sessionId": "e5243e",
            "runId": "post-fix",
            "hypothesisId": "H7",
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


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.error(f"Application error: {exc.message}")
    _debug_log(
        "src/presentation/middleware/error_handler.py:38",
        "AppException handler invoked",
        {"path": request.url.path, "detail": exc.message},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.error(f"Validation error: {exc.errors()}")
    _debug_log(
        "src/presentation/middleware/error_handler.py:51",
        "Validation handler invoked",
        {"path": request.url.path, "error_count": len(exc.errors())},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.exception("Unexpected error occurred")
    _debug_log(
        "src/presentation/middleware/error_handler.py:64",
        "General exception handler invoked",
        {"path": request.url.path, "error_type": type(exc).__name__},
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
