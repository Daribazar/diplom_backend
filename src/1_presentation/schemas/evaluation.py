"""Evaluation schemas."""
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class SubmitTestRequest(BaseModel):
    """Test submission request."""
    answers: List[Dict]  # [{"question_id": "q1", "answer": "Option A"}]


class QuestionResultResponse(BaseModel):
    """Individual question result."""
    question_id: str
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
