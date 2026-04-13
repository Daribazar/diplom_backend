from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json
from pathlib import Path
from datetime import datetime, timezone

from src.config import settings
from src.core.dependencies import get_db
from src.core.exceptions import AppException
from src.presentation.api.v1.router import api_router
from src.presentation.middleware.logging import LoggingMiddleware
from src.presentation.middleware.error_handler import (
    app_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)

DEBUG_LOG_PATH = Path("/Users/daribazar/Documents/diplom/.cursor/debug-e5243e.log")


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict) -> None:
    # region agent log
    try:
        payload = {
            "sessionId": "e5243e",
            "runId": "pre-fix",
            "hypothesisId": hypothesis_id,
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

app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic AI system for personalized learning",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(api_router)


@app.on_event("startup")
async def debug_startup_probe() -> None:
    middleware_names = [m.cls.__name__ for m in app.user_middleware]
    exception_handler_keys = [str(key) for key in app.exception_handlers.keys()]
    _debug_log(
        "H1",
        "src/main.py:44",
        "Startup middleware and handlers snapshot",
        {
            "middlewares": middleware_names,
            "hasLoggingMiddleware": "LoggingMiddleware" in middleware_names,
            "hasCustomValidationHandler": any("RequestValidationError" in key for key in exception_handler_keys),
            "hasCustomAppExceptionHandler": any("AppException" in key for key in exception_handler_keys),
            "exceptionHandlerCount": len(exception_handler_keys),
            "allowOrigins": settings.CORS_ALLOW_ORIGINS,
            "allowCredentials": True,
        },
    )


@app.get("/")
async def root():
    """Health check endpoint."""
    _debug_log(
        "H4",
        "src/main.py:79",
        "Root endpoint called",
        {"appEnv": settings.APP_ENV},
    )
    return JSONResponse(
        content={
            "status": "running",
            "app": settings.APP_NAME,
            "version": "0.1.0",
            "environment": settings.APP_ENV
        }
    )


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Detailed health check with database connectivity."""
    db_status = "disconnected"
    redis_status = "disconnected"
    
    try:
        result = await db.execute(text("SELECT 1"))
        if result:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    try:
        import redis
        r = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        r.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    
    _debug_log(
        "H4",
        "src/main.py:112",
        "Health endpoint statuses",
        {"db_status": db_status, "redis_status": redis_status},
    )

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "redis": redis_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
