"""Get course lectures use case."""
from typing import List
from src.3_domain.entities.lecture import Lecture
from src.4_infrastructure.database.repositories.lecture_repository import LectureRepository
from src.4_infrastructure.database.repositories.course_repository import CourseRepository
from src.core.exceptions import NotFoundError, UnauthorizedError


class GetCourseLecturesUseCase:
    """Use case: Get all lectures for a course."""
    
    def __init__(
        self,
        lecture_repository: LectureRepository,
        course_repository: CourseRepository
    ):
        """Initialize use case with repositories."""
        self.lecture_repo = lecture_repository
        self.course_repo = course_repository
    
    async def execute(self, course_id: str, user_id: str) -> List[Lecture]:
        """
        Get all lectures for a course.
        
        Business rules:
        - Course must exist
        - User must own the course
        - Lectures sorted by week number
        
        Args:
            course_id: Course ID
            user_id: User ID requesting access
            
        Returns:
            List of Lecture entities
            
        Raises:
            NotFoundError: If course doesn't exist
            UnauthorizedError: If user doesn't own course
        """
        # Check course exists and user owns it
        course = await self.course_repo.get_by_id(course_id)
        
        if not course:
            raise NotFoundError(f"Course {course_id} not found")
        
        if course.owner_id != user_id:
            raise UnauthorizedError("You don't have access to this course")
        
        # Get lectures
        lectures = await self.lecture_repo.get_by_course(course_id)
        
        return lectures
