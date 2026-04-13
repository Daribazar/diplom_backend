"""Common shared schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        from_attributes = True


class PaginationParams(BaseModel):
    """Pagination parameters."""

    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    total: int
    skip: int
    limit: int
    items: list


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    status_code: int
    timestamp: datetime = datetime.utcnow()
