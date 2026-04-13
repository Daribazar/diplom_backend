"""API route dependencies.

Re-exports shared auth dependencies from src.core.dependencies to avoid
duplicating JWT parsing logic in multiple places.
"""

from fastapi import Depends

from src.core.dependencies import CurrentUser, get_current_user, get_db


async def get_current_user_id(
    current_user: CurrentUser = Depends(get_current_user),
) -> str:
    """Compatibility helper: returns current authenticated user ID."""
    return current_user.id
