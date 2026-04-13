"""Evaluation schemas."""
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class SubmitAnswerItem(BaseModel):
    """Single answer item in a test submission."""
    question_id: str
    answer: str


class SubmitTestRequest(BaseModel):
    """Test submission request."""
    answers: List[SubmitAnswerItem]


class QuestionResultResponse(BaseModel):
    """Individual question result."""
    question_id: str
    question_text: str
    student_answer: str
    correct_answer: str
    is_correct: bool
    points_earned: float
    max_points: int
    feedback: str


class EvaluationResponse(BaseModel):
    """Test evaluation response."""
    attempt_id: str
    test_id: str
    total_score: float
    percentage: float
    status: str
    answers: List[QuestionResultResponse]
    weak_topics: List[str]
    analytics: Dict
    overall_feedback: str
    created_at: datetime


class AttemptSummaryResponse(BaseModel):
    """Compact attempt info for listing."""
    attempt_id: str
    total_score: float
    percentage: float
    status: str
    created_at: Optional[str]


class TestAttemptsResponse(BaseModel):
    """All attempts by current user for a test."""
    test_id: str
    total_attempts: int
    attempts: List[AttemptSummaryResponse]
