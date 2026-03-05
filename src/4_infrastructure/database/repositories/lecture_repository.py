"""Lecture repository implementation."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.3_domain.entities.lecture import Lecture
from src.4_infrastructure.database.models.lecture import LectureModel


class LectureRepository:
    """Lecture repository - implements domain interface."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session
    
    async def create(self, lecture: Lecture) -> Lecture:
        """Create lecture in database."""
        db_lecture = LectureModel(
            id=lecture.id,
            course_id=lecture.course_id,
            week_number=lecture.week_number,
            title=lecture.title,
            file_url=lecture.file_url,
            content=lecture.content,
            status=lecture.status,
            key_concepts=lecture.key_concepts,
            embedding_ids=lecture.embedding_ids,
            metadata={}
        )
        self.session.add(db_lecture)
        await self.session.flush()
        await self.session.refresh(db_lecture)
        return self._to_entity(db_lecture)
    
    async def get_by_id(self, lecture_id: str) -> Optional[Lecture]:
        """Find lecture by ID."""
        result = await self.session.execute(
            select(LectureModel).where(LectureModel.id == lecture_id)
        )
        db_lecture = result.scalar_one_or_none()
        if not db_lecture:
            return None
        return self._to_entity(db_lecture)
    
    async def get_by_course_and_week(
        self,
        course_id: str,
        week_number: int
    ) -> Optional[Lecture]:
        """Get lecture by course and week."""
        result = await self.session.execute(
            select(LectureModel).where(
                LectureModel.course_id == course_id,
                LectureModel.week_number == week_number
            )
        )
        db_lecture = result.scalar_one_or_none()
        if not db_lecture:
            return None
        return self._to_entity(db_lecture)
    
    async def get_by_course(self, course_id: str) -> List[Lecture]:
        """Get all lectures for a course."""
        result = await self.session.execute(
            select(LectureModel)
            .where(LectureModel.course_id == course_id)
            .order_by(LectureModel.week_number.asc())
        )
        lectures = result.scalars().all()
        return [self._to_entity(lec) for lec in lectures]
    
    async def update(self, lecture: Lecture) -> Lecture:
        """Update lecture."""
        result = await self.session.execute(
            select(LectureModel).where(LectureModel.id == lecture.id)
        )
        db_lecture = result.scalar_one_or_none()
        if not db_lecture:
            raise ValueError(f"Lecture {lecture.id} not found")
        
        db_lecture.title = lecture.title
        db_lecture.content = lecture.content
        db_lecture.status = lecture.status
        db_lecture.file_url = lecture.file_url
        db_lecture.key_concepts = lecture.key_concepts
        db_lecture.embedding_ids = lecture.embedding_ids
        
        await self.session.flush()
        await self.session.refresh(db_lecture)
        return self._to_entity(db_lecture)
    
    async def delete(self, lecture_id: str) -> bool:
        """Delete lecture."""
        result = await self.session.execute(
            select(LectureModel).where(LectureModel.id == lecture_id)
        )
        lecture = result.scalar_one_or_none()
        if not lecture:
            return False
        
        await self.session.delete(lecture)
        return True
    
    def _to_entity(self, db_model: LectureModel) -> Lecture:
        """Convert database model to domain entity."""
        return Lecture(
            id=db_model.id,
            course_id=db_model.course_id,
            week_number=db_model.week_number,
            title=db_model.title,
            status=db_model.status,
            content=db_model.content,
            file_url=db_model.file_url,
            key_concepts=db_model.key_concepts or [],
            embedding_ids=db_model.embedding_ids or [],
            created_at=db_model.created_at
        )
