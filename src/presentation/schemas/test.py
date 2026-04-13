"""Test schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class TestGenerateRequest(BaseModel):
    """Test generation request."""

    week_number: int = Field(ge=1, le=16, description="Week number (1-16)")
    difficulty: str = Field(
        default="medium", pattern="^(easy|medium|hard)$", description="Difficulty level"
    )
    question_types: List[str] = Field(
        default=["mcq", "true_false"], description="Question types"
    )
    question_count: int = Field(
        default=10, ge=5, le=20, description="Number of questions"
    )


class QuestionResponse(BaseModel):
    """Question response."""

    question_id: str
    type: str
    question_text: str
    options: Optional[List[str]] = None
    points: int
    difficulty: str
    bloom_level: Optional[str] = None


class TestResponse(BaseModel):
    """Test response."""

    id: str
    lecture_id: str
    title: str
    difficulty: str
    total_points: int
    time_limit: int
    questions: List[QuestionResponse]
    created_at: datetime


class TestListResponse(BaseModel):
    """Test list response."""

    total: int
    tests: List[TestResponse]
