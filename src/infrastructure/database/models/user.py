"""User SQLAlchemy model."""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from src.infrastructure.database.models.base import Base, TimestampMixin
import uuid


class UserModel(Base, TimestampMixin):
    """User database model."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    courses = relationship("CourseModel", back_populates="owner", cascade="all, delete-orphan")
    attempts = relationship("StudentAttemptModel", back_populates="student", cascade="all, delete-orphan")
