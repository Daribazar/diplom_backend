"""Test repository."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.test import Test
from src.infrastructure.database.models.test import TestModel


class TestRepository:
    """Repository for tests."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository."""
        self.session = session
    
    async def create(self, test: Test) -> Test:
        """
        Create test.
        
        Args:
            test: Test entity
            
        Returns:
            Created test
        """
        print(f"[TestRepository] Creating test {test.id}")
        print(f"[TestRepository] Questions count: {len(test.questions) if test.questions else 0}")
        print(f"[TestRepository] Questions data: {test.questions[:2] if test.questions else 'None'}")  # First 2 questions
        
        db_test = TestModel(
            id=test.id,
            lecture_id=test.lecture_id,
            title=test.title,
            difficulty=test.difficulty,
            total_points=test.total_points,
            time_limit=test.time_limit,
            questions=test.questions
        )
        
        self.session.add(db_test)
        await self.session.flush()
        await self.session.refresh(db_test)
        
        print(f"[TestRepository] Test saved. DB questions count: {len(db_test.questions) if db_test.questions else 0}")
        
        return self._to_entity(db_test)
    
    async def get_by_id(self, test_id: str) -> Optional[Test]:
        """Get test by ID."""
        result = await self.session.execute(
            select(TestModel).where(TestModel.id == test_id)
        )
        db_test = result.scalar_one_or_none()
        
        if not db_test:
            return None
        
        return self._to_entity(db_test)
    
    async def get_by_lecture(self, lecture_id: str) -> List[Test]:
        """Get all tests for a lecture."""
        result = await self.session.execute(
            select(TestModel)
            .where(TestModel.lecture_id == lecture_id)
            .order_by(TestModel.created_at.desc())
        )
        tests = result.scalars().all()
        
        return [self._to_entity(t) for t in tests]
    
    def _to_entity(self, db_model: TestModel) -> Test:
        """Convert database model to entity."""
        return Test(
            id=db_model.id,
            lecture_id=db_model.lecture_id,
            title=db_model.title,
            difficulty=db_model.difficulty,
            total_points=db_model.total_points,
            time_limit=db_model.time_limit,
            questions=db_model.questions,
            created_at=db_model.created_at
        )
