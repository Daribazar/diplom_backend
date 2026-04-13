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
    status: ProcessingStatus
    message: str
    estimated_time: str = "2-3 minutes"


class LectureResponse(BaseModel):
    """Lecture response."""
    id: str
    course_id: str
    week_number: int
    title: str
    status: ProcessingStatus
    key_concepts: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LectureListResponse(BaseModel):
    """Lecture list response."""
    total: int
    lectures: List[LectureResponse]


class LectureProcessResponse(BaseModel):
    """Lecture process trigger response."""
    message: str
    lecture_id: str
    key_concepts: List[str]
    chunks_created: int
    llm_usage: dict


class LectureStatusResponse(BaseModel):
    """Lecture processing status response."""
    lecture_id: str
    title: str
    status: ProcessingStatus
    key_concepts: List[str]
    created_at: Optional[str]
    processed_at: Optional[str]
