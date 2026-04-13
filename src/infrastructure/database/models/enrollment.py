"""Course enrollment model."""

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from src.infrastructure.database.models.base import Base


class CourseEnrollmentModel(Base):
    """Course enrollment model for student enrollment requests."""

    __tablename__ = "course_enrollments"

    id = Column(String, primary_key=True)
    course_id = Column(
        String, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    student_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(
        String(20), nullable=False, default="pending"
    )  # pending, approved, rejected
    requested_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_enrollments_course", "course_id"),
        Index("ix_enrollments_student", "student_id"),
        Index("ix_enrollments_status", "status"),
    )
