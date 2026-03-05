"""Test database connection."""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import text
from src.4_infrastructure.database.connection import async_session_maker
from src.config import settings


async def test_connection():
    """Test database connection and basic operations."""
    print(f"Testing connection to: {settings.DATABASE_URL}")
    
    try:
        async with async_session_maker() as session:
            # Test basic query
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Database connection successful! Test query result: {row[0]}")
            
            # Test version
            result = await session.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"✅ PostgreSQL version: {version[0]}")
            
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
