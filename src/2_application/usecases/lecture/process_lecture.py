"""Process lecture use case."""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.2_application.orchestrators.agent_orchestrator import AgentOrchestrator
from src.4_infrastructure.database.repositories.lecture_repository import LectureRepository
from src.4_infrastructure.database.repositories.course_repository import CourseRepository
from src.core.exceptions import NotFoundError


class ProcessLectureUseCase:
    """Use case for processing lecture content (chunking, embedding)."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize use case.
        
        Args:
            db: Database session
        """
        self.db = db
        self.lecture_repo = LectureRepository(db)
        self.course_repo = CourseRepository(db)
        self.orchestrator = AgentOrchestrator(db)
    
    async def execute(
        self,
        lecture_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Execute lecture processing.
        
        Args:
            lecture_id: Lecture ID
            user_id: User ID (for ownership validation)
            
        Returns:
            Processing results
            
        Raises:
            NotFoundError: If lecture not found
            PermissionError: If user doesn't own the course
        """
        # Get lecture
        db_lecture = await self.lecture_repo.get_by_id(lecture_id)
        if not db_lecture:
            raise NotFoundError(f"Lecture {lecture_id} not found")
        
        # Validate ownership
        db_course = await self.course_repo.get_by_id(db_lecture.course_id)
        if not db_course or db_course.user_id != user_id:
            raise PermissionError("Not authorized to process this lecture")
        
        # Validate lecture has content
        if not db_lecture.content:
            raise ValueError("Lecture has no content to process")
        
        # Mark as processing
        db_lecture.status = "processing"
        await self.db.commit()
        
        try:
            # Process through orchestrator
            result = await self.orchestrator.process_lecture(
                lecture_id=lecture_id,
                content=db_lecture.content,
                title=db_lecture.title
            )
            
            return result
            
        except Exception as e:
            # Mark as failed
            db_lecture.status = "failed"
            await self.db.commit()
            raise RuntimeError(f"Lecture processing failed: {str(e)}")

