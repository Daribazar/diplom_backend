"""Analytics schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class AnalyticsOverviewResponse(BaseModel):
    """Overall analytics overview."""
    total_score_average: float = Field(..., description="Average score across all tests")
    total_tests: int = Field(..., description="Total number of tests completed")
    average_time_minutes: int = Field(..., description="Average time spent per test")
    highest_score: float = Field(..., description="Highest score achieved")
    highest_score_course: Optional[str] = Field(None, description="Course code with highest score")
    score_change: float = Field(..., description="Score change percentage")
    tests_change: int = Field(..., description="Change in number of tests")
    time_change: int = Field(..., description="Change in average time")


class WeeklyScoreData(BaseModel):
    """Weekly score data point."""
    week: str = Field(..., description="Week label")
    score: float = Field(..., description="Average score for the week")


class BloomTaxonomyData(BaseModel):
    """Bloom's Taxonomy performance data."""
    category: str = Field(..., description="Bloom's taxonomy category")
    score: float = Field(..., description="Performance score for this category")


class TopicMasteryData(BaseModel):
    """Topic mastery data."""
    topic: str = Field(..., description="Topic name")
    mastery: float = Field(..., description="Mastery percentage")


class CourseComparisonData(BaseModel):
    """Course comparison data."""
    course_code: str = Field(..., description="Course code")
    course_name: str = Field(..., description="Course name")
    average_score: float = Field(..., description="Average score in this course")
    test_count: int = Field(..., description="Number of tests taken")


class CoursePerformanceData(BaseModel):
    """Detailed course performance data."""
    course_id: str = Field(..., description="Course ID")
    course_name: str = Field(..., description="Course name")
    course_code: str = Field(..., description="Course code")
    instructor: str = Field(..., description="Instructor name")
    average_score: float = Field(..., description="Average score")
    tests_completed: int = Field(..., description="Number of tests completed")
    lectures_uploaded: int = Field(..., description="Number of lectures uploaded")
    color: str = Field(..., description="Color for visualization")
