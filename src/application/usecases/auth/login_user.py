"""User login use case."""

from datetime import timedelta
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.core.security import verify_password, create_access_token
from src.core.exceptions import InvalidCredentialsError
from src.config import settings


class LoginUserUseCase:
    """Use case: User login."""

    def __init__(self, user_repository: UserRepository):
        """Initialize use case with repository."""
        self.user_repo = user_repository

    async def execute(self, email: str, password: str) -> str:
        """
        Authenticate user and return JWT token.

        Business rules:
        - Email must exist
        - Password must match
        - User must be active

        Args:
            email: User email address
            password: Plain text password

        Returns:
            JWT access token

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        # Get user (with hashed password)
        user_model = await self.user_repo.get_by_email(email)
        if not user_model:
            raise InvalidCredentialsError("Invalid email or password")

        # Verify password
        if not verify_password(password, user_model.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        # Check if active
        if not user_model.is_active:
            raise InvalidCredentialsError("Inactive user")

        # Create JWT token
        access_token = create_access_token(
            data={"sub": user_model.id},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return access_token
