"""Initialize database with tables."""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine
from src.config import settings
from src.infrastructure.database.models.base import Base
from src.infrastructure.database.models import (
    UserModel,
    CourseModel,
    LectureModel,
    TestModel,
    StudentAttemptModel
)


async def init_db():
    """Create all database tables."""
    print(f"Connecting to database: {settings.DATABASE_URL}")
    
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Database initialized successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())
