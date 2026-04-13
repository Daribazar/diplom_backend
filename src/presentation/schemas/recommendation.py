"""Recommendation schemas."""
from pydantic import BaseModel, Field
from typing import List, Literal


class FocusArea(BaseModel):
    """Weak topic focus area."""
    topic: str
    percentage: int
    priority: Literal["high", "medium", "low"]


class StudyTask(BaseModel):
    """Single study task."""
    duration: int = Field(..., description="Estimated minutes")
    description: str


class StudyPlanDay(BaseModel):
    """Single day in study plan."""
    day: int
    title: str
    tasks: List[StudyTask]


class CourseRecommendationResponse(BaseModel):
    """Personalized recommendation response."""
    course_id: str
    based_on_week: int
    focus_areas: List[FocusArea]
    study_plan: List[StudyPlanDay]
    ai_advice: str
