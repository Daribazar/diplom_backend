"""User registration use case."""
import uuid
from src.domain.entities.user import User
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.core.security import get_password_hash
from src.core.exceptions import DuplicateEmailError


class RegisterUserUseCase:
    """Use case: Register new user."""
    
    def __init__(self, user_repository: UserRepository):
        """Initialize use case with repository."""
        self.user_repo = user_repository
    
    async def execute(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str = "student"
    ) -> User:
        """
        Register new user.
        
        Business rules:
        - Email must be unique
        - Password must be hashed
        - User starts as active
        - Role can be student or teacher
        
        Args:
            email: User email address
            password: Plain text password
            full_name: User's full name
            role: User role (student or teacher)
            
        Returns:
            Created User entity
            
        Raises:
            DuplicateEmailError: If email already exists
        """
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise DuplicateEmailError("Email already registered")
        
        # Create domain entity
        user = User(
            id=f"user_{uuid.uuid4().hex[:12]}",
            email=email,
            full_name=full_name,
            is_active=True,
            role=role
        )
        
        # Hash password (infrastructure concern)
        hashed_password = get_password_hash(password)
        
        # Persist to database
        created_user = await self.user_repo.create(user, hashed_password)
        
        return created_user
