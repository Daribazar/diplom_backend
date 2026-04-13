"""Test SQLAlchemy model."""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from src.infrastructure.database.models.base import Base, TimestampMixin
import uuid


class TestModel(Base, TimestampMixin):
    """Test database model."""

    __tablename__ = "tests"

    id = Column(
        String, primary_key=True, default=lambda: f"test_{uuid.uuid4().hex[:12]}"
    )
    lecture_id = Column(
        String, ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False
    )
    created_by = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title = Column(String(200), nullable=False)
    difficulty = Column(String(20), nullable=False)  # easy, medium, hard
    total_points = Column(Integer, default=0)
    time_limit = Column(Integer, default=30)  # minutes

    # JSONB for flexible question structure
    questions = Column(JSONB, nullable=False, default=list)

    # Relationships
    lecture = relationship("LectureModel", back_populates="tests")
    attempts = relationship(
        "StudentAttemptModel", back_populates="test", cascade="all, delete-orphan"
    )
