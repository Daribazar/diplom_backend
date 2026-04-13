"""Dashboard schemas."""

from pydantic import BaseModel, Field


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response."""

    total_courses: int = Field(..., description="Total number of courses")
    total_lectures: int = Field(..., description="Total number of lectures uploaded")
    total_tests: int = Field(..., description="Total number of tests taken")
    average_score: float = Field(..., description="Average score across all tests")


class DashboardCourseData(BaseModel):
    """Course data for dashboard."""

    id: str = Field(..., description="Course ID")
    name: str = Field(..., description="Course name")
    code: str = Field(..., description="Course code")
    semester: str = Field(..., description="Semester")
    instructor: str = Field(..., description="Instructor name")
    color: str = Field(..., description="Course color")
    lectures_uploaded: int = Field(..., description="Number of lectures uploaded")
    tests_completed: int = Field(..., description="Number of tests completed")
    average_score: float = Field(..., description="Average score in this course")
