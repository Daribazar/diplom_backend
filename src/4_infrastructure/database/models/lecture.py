"""Lecture SQLAlchemy model."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from src.4_infrastructure.database.models.base import Base, TimestampMixin
import uuid


class LectureModel(Base, TimestampMixin):
    """Lecture database model with JSONB for flexible data."""
    
    __tablename__ = "lectures"
    
    id = Column(String, primary_key=True, default=lambda: f"lec_{uuid.uuid4().hex[:12]}")
    course_id = Column(String, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    week_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    file_url = Column(String, nullable=True)
    content = Column(Text, nullable=True)  # Processed text
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    
    # JSONB columns for flexible data
    key_concepts = Column(JSONB, default=list)
    embedding_ids = Column(JSONB, default=list)
    metadata = Column(JSONB, default=dict)
    
    # Relationships
    course = relationship("CourseModel", back_populates="lectures")
    tests = relationship("TestModel", back_populates="lecture", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('week_number >= 1 AND week_number <= 16', name='valid_week_number'),
        UniqueConstraint('course_id', 'week_number', name='unique_lecture_per_week'),
    )
