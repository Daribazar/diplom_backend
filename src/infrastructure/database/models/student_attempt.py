"""Student attempt SQLAlchemy model."""
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from src.infrastructure.database.models.base import Base, TimestampMixin
import uuid


class StudentAttemptModel(Base, TimestampMixin):
    """Student test attempt database model."""
    
    __tablename__ = "student_attempts"
    
    id = Column(String, primary_key=True, default=lambda: f"attempt_{uuid.uuid4().hex[:12]}")
    student_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_id = Column(String, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    total_score = Column(Float, default=0.0)
    percentage = Column(Float, default=0.0)
    status = Column(String(20), default="in_progress")  # in_progress, submitted, graded
    
    # JSONB columns
    answers = Column(JSONB, default=list)
    weak_topics = Column(JSONB, default=list)
    analytics = Column(JSONB, default=dict)
    
    # Relationships
    student = relationship("UserModel", back_populates="attempts")
    test = relationship("TestModel", back_populates="attempts")
