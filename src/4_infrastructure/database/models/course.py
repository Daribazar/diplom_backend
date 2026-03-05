"""Course SQLAlchemy model."""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from src.4_infrastructure.database.models.base import Base, TimestampMixin
import uuid


class CourseModel(Base, TimestampMixin):
    """Course database model."""
    
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True, default=lambda: f"course_{uuid.uuid4().hex[:12]}")
    name = Column(String(200), nullable=False)
    code = Column(String(20), nullable=False)
    semester = Column(String(50), nullable=False)
    instructor = Column(String(200), nullable=True)
    owner_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    owner = relationship("UserModel", back_populates="courses")
    lectures = relationship("LectureModel", back_populates="course", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('owner_id', 'code', 'semester', name='unique_course_per_semester'),
    )
