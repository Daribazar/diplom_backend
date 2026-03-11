"""Student attempt repository."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.student_attempt import StudentAttempt
from src.infrastructure.database.models.student_attempt import StudentAttemptModel


class StudentAttemptRepository:
    """Repository for student attempts."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        self.session = session
    
    async def create(self, attempt: StudentAttempt) -> StudentAttempt:
        """
        Create attempt.
        
        Args:
            attempt: StudentAttempt entity
            
        Returns:
            Created attempt
        """
        db_attempt = StudentAttemptModel(
            id=attempt.id,
            student_id=attempt.student_id,
            test_id=attempt.test_id,
            total_score=attempt.total_score,
            percentage=attempt.percentage,
            status=attempt.status,
            answers=attempt.answers,
            weak_topics=attempt.weak_topics,
            analytics=attempt.analytics
            # Note: submitted_at is not in the model, using created_at instead
        )
        
        self.session.add(db_attempt)
        await self.session.flush()
        await self.session.refresh(db_attempt)
        
        return self._to_entity(db_attempt)
    
    async def get_by_id(self, attempt_id: str) -> Optional[StudentAttempt]:
        """Get attempt by ID."""
        result = await self.session.execute(
            select(StudentAttemptModel).where(StudentAttemptModel.id == attempt_id)
        )
        db_attempt = result.scalar_one_or_none()
        
        if not db_attempt:
            return None
        
        return self._to_entity(db_attempt)
    
    async def get_by_student_and_test(
        self,
        student_id: str,
        test_id: str
    ) -> List[StudentAttempt]:
        """Get all attempts by student for a test."""
        result = await self.session.execute(
            select(StudentAttemptModel).where(
                StudentAttemptModel.student_id == student_id,
                StudentAttemptModel.test_id == test_id
            ).order_by(StudentAttemptModel.created_at.desc())
        )
        attempts = result.scalars().all()
        
        return [self._to_entity(a) for a in attempts]
    
    def _to_entity(self, db_model: StudentAttemptModel) -> StudentAttempt:
        """Convert database model to entity."""
        return StudentAttempt(
            id=db_model.id,
            student_id=db_model.student_id,
            test_id=db_model.test_id,
            total_score=db_model.total_score,
            percentage=db_model.percentage,
            status=db_model.status,
            answers=db_model.answers,
            weak_topics=db_model.weak_topics,
            analytics=db_model.analytics,
            created_at=db_model.created_at,
            submitted_at=db_model.created_at  # Use created_at as submitted_at
        )
