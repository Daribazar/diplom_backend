from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.config import settings
from src.core.dependencies import get_db
from src.presentation.api.v1.router import api_router

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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.18.0.6:3000",  # Docker network
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


@app.get("/")
async def root():
    """Health check endpoint."""
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
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        if result:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    # Test Redis connection
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=1)
        r.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"
    
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
