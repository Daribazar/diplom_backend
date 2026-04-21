import redis
from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.dependencies import get_db
from src.core.exceptions import AppException
from src.presentation.api.v1.router import api_router
from src.presentation.middleware.error_handler import (
    app_exception_handler,
    general_exception_handler,
    validation_exception_handler,
)
from src.presentation.middleware.logging import LoggingMiddleware


app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic AI system for personalized learning",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

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


@app.get("/")
async def root():
    """Root / liveness probe."""
    return {
        "status": "running",
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.APP_ENV,
    }


async def _check_db(db: AsyncSession) -> str:
    try:
        await db.execute(text("SELECT 1"))
        return "connected"
    except Exception as e:
        return f"error: {e}"


def _check_redis() -> str:
    try:
        redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1).ping()
        return "connected"
    except Exception:
        return "disconnected"


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    """Readiness probe with DB + Redis connectivity."""
    db_status = await _check_db(db)
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "redis": _check_redis(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
