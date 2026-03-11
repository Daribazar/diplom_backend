"""Course schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CourseCreate(BaseModel):
    """Course creation request."""
    name: str = Field(..., min_length=1, max_length=200)
    code: str = Field(..., min_length=1, max_length=20)
    semester: str = Field(..., min_length=1, max_length=50)
    instructor: Optional[str] = Field(None, max_length=200)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Introduction to Machine Learning",
                "code": "CS401",
                "semester": "Fall 2024",
                "instructor": "Prof. Smith"
            }
        }


class CourseUpdate(BaseModel):
    """Course update request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    instructor: Optional[str] = Field(None, max_length=200)


class CourseResponse(BaseModel):
    """Course response."""
    id: str
    name: str
    code: str
    semester: str
    instructor: Optional[str]
    owner_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CourseListResponse(BaseModel):
    """Course list response."""
    total: int
    courses: list[CourseResponse]
