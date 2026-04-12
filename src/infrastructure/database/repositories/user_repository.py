"""User repository implementation."""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.user import User
from src.infrastructure.database.models.user import UserModel


class UserRepository:
    """User repository - implements domain interface."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, user: User, hashed_password: str) -> User:
        """Create user in database."""
        db_user = UserModel(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=user.is_active,
            role=user.role
        )
        self.session.add(db_user)
        await self.session.flush()
        await self.session.refresh(db_user)
        return self._to_entity(db_user)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return self._to_entity(db_user)
    
    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """Find user by email - returns model for password check."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()
    
    def _to_entity(self, db_model: UserModel) -> User:
        """Convert database model to domain entity."""
        return User(
            id=db_model.id,
            email=db_model.email,
            full_name=db_model.full_name,
            is_active=db_model.is_active,
            role=db_model.role,
            created_at=db_model.created_at
        )
