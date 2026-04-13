"""Helpers for consistent domain-exception to HTTPException mapping."""
from fastapi import HTTPException, status

from src.core.exceptions import AppException, NotFoundError, UnauthorizedError, DuplicateError


def map_common_domain_error(error: Exception) -> HTTPException:
    """Map common domain exceptions to HTTPException."""
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, UnauthorizedError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, DuplicateError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    if isinstance(error, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, AppException):
        headers = {"WWW-Authenticate": "Bearer"} if error.status_code == status.HTTP_401_UNAUTHORIZED else None
        return HTTPException(status_code=error.status_code, detail=error.message, headers=headers)
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
    )
