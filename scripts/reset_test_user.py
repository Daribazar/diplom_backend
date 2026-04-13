#!/usr/bin/env python3
"""
Reset test user for API testing
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from src.infrastructure.database.connection import get_db
from src.infrastructure.database.models.user import UserModel
from src.core.security import get_password_hash


async def reset_test_user():
    """Delete and recreate test user"""
    print("Resetting test user...")

    async for session in get_db():
        try:
            # Delete existing test user
            result = await session.execute(
                select(UserModel).where(UserModel.email == "test@example.com")
            )
            existing_user = result.scalar_one_or_none()

            if existing_user:
                print(f"Found existing user: {existing_user.id}")
                await session.delete(existing_user)
                await session.commit()
                print("✅ Deleted existing test user")
            else:
                print("No existing test user found")

            # Create new test user
            hashed_password = get_password_hash("test123456")
            new_user = UserModel(
                email="test@example.com",
                hashed_password=hashed_password,
                full_name="Test User",
                is_active=True,
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            print(f"✅ Created new test user: {new_user.id}")
            print(f"   Email: {new_user.email}")
            print(f"   Password: test123456")

        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
        finally:
            break


if __name__ == "__main__":
    asyncio.run(reset_test_user())
