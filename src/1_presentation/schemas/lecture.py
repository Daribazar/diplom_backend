"""Lecture schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Lecture processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LectureUploadResponse(BaseModel):
    """Lecture upload response."""
    id: str
    course_id: str
    week_number: int
    title: str
    status: str
    message: str
    estimated_time: str = "2-3 minutes"


class LectureResponse(BaseModel):
    """Lecture response."""
    id: str
    course_id: str
    week_number: int
    title: str
    status: str
    key_concepts: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LectureListResponse(BaseModel):
    """Lecture list response."""
    total: int
    lectures: List[LectureResponse]
