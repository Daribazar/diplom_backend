"""Authentication endpoints."""

from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, CurrentUser
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.application.usecases.auth.register_user import RegisterUserUseCase
from src.application.usecases.auth.login_user import LoginUserUseCase
from src.presentation.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
)
from src.core.exceptions import DuplicateEmailError, InvalidCredentialsError
from src.presentation.api.http_errors import map_common_domain_error

router = APIRouter()


def _to_user_response(user) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        role=user.role,
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email and password",
)
async def register(
    user_data: UserRegister, db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Register new user.

    - **email**: Valid email address (must be unique)
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    """
    user_repo = UserRepository(db)
    use_case = RegisterUserUseCase(user_repo)

    try:
        user = await use_case.execute(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role,
        )

        return _to_user_response(user)
    except DuplicateEmailError as e:
        raise map_common_domain_error(e)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login user",
    description="Authenticate user and receive JWT access token",
)
async def login(credentials: UserLogin, db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Login user and return JWT token.

    - **email**: User's email address
    - **password**: User's password

    Returns JWT token to use in Authorization header:
    `Authorization: Bearer <token>`
    """
    user_repo = UserRepository(db)
    use_case = LoginUserUseCase(user_repo)

    try:
        access_token = await use_case.execute(
            email=credentials.email, password=credentials.password
        )

        return TokenResponse(access_token=access_token, token_type="bearer")
    except InvalidCredentialsError as e:
        raise map_common_domain_error(e)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user",
)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user info.

    Requires valid JWT token in Authorization header.
    """
    return _to_user_response(current_user)
