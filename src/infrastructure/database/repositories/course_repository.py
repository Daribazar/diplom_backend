"""Course repository implementation."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.entities.course import Course
from src.infrastructure.database.models.course import CourseModel
from src.core.exceptions import NotFoundError


class CourseRepository:
    """Course repository - implements domain interface."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, course: Course) -> Course:
        """Create course in database."""
        db_course = CourseModel(
            id=course.id,
            name=course.name,
            code=course.code,
            semester=course.semester,
            instructor=course.instructor,
            owner_id=course.owner_id
        )
        self.session.add(db_course)
        await self.session.flush()
        await self.session.refresh(db_course)
        return self._to_entity(db_course)
    
    async def get_by_id(self, course_id: str) -> Optional[Course]:
        """Find course by ID."""
        result = await self.session.execute(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        db_course = result.scalar_one_or_none()
        if not db_course:
            return None
        return self._to_entity(db_course)
    
    async def get_by_owner(self, owner_id: str) -> List[Course]:
        """Get all courses for a user."""
        result = await self.session.execute(
            select(CourseModel)
            .where(CourseModel.owner_id == owner_id)
            .order_by(CourseModel.created_at.desc())
        )
        courses = result.scalars().all()
        return [self._to_entity(c) for c in courses]
    
    async def update(self, course: Course) -> Course:
        """Update course."""
        result = await self.session.execute(
            select(CourseModel).where(CourseModel.id == course.id)
        )
        db_course = result.scalar_one_or_none()
        if not db_course:
            raise NotFoundError(f"Course {course.id} not found")
        
        db_course.name = course.name
        db_course.code = course.code
        db_course.instructor = course.instructor
        
        await self.session.flush()
        await self.session.refresh(db_course)
        return self._to_entity(db_course)
    
    async def delete(self, course_id: str) -> bool:
        """Delete course."""
        result = await self.session.execute(
            select(CourseModel).where(CourseModel.id == course_id)
        )
        course = result.scalar_one_or_none()
        if not course:
            return False
        
        await self.session.delete(course)
        return True
    
    def _to_entity(self, db_model: CourseModel) -> Course:
        """Convert database model to domain entity."""
        return Course(
            id=db_model.id,
            name=db_model.name,
            code=db_model.code,
            semester=db_model.semester,
            owner_id=db_model.owner_id,
            instructor=db_model.instructor,
            created_at=db_model.created_at
        )
