"""Enrollment schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EnrollmentRequest(BaseModel):
    """Enrollment request schema."""
    course_id: str = Field(..., description="Course ID to enroll in")


class EnrollmentResponse(BaseModel):
    """Enrollment response schema."""
    id: str = Field(..., description="Enrollment ID")
    course_id: str = Field(..., description="Course ID")
    student_id: str = Field(..., description="Student ID")
    student_name: str = Field(..., description="Student full name")
    student_email: str = Field(..., description="Student email")
    status: str = Field(..., description="Enrollment status: pending, approved, rejected")
    requested_at: datetime = Field(..., description="Request timestamp")
    approved_at: Optional[datetime] = Field(None, description="Approval timestamp")


class EnrollmentApprovalRequest(BaseModel):
    """Enrollment approval/rejection schema."""
    enrollment_id: str = Field(..., description="Enrollment ID")
    approve: bool = Field(..., description="True to approve, False to reject")


class EnrollmentListResponse(BaseModel):
    """List of enrollments."""
    total: int = Field(..., description="Total number of enrollments")
    enrollments: list[EnrollmentResponse] = Field(..., description="List of enrollments")


class CourseWithEnrollmentStatus(BaseModel):
    """Course with enrollment status for student."""
    id: str
    name: str
    code: str
    semester: str
    instructor: str
    color: str
    enrollment_status: Optional[str] = Field(None, description="pending, approved, rejected, or None if not enrolled")
    is_enrolled: bool = Field(False, description="Whether student is enrolled")
