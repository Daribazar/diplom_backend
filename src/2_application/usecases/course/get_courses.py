"""Get courses use case."""
from typing import List
from src.3_domain.entities.course import Course
from src.4_infrastructure.database.repositories.course_repository import CourseRepository


class GetCoursesUseCase:
    """Use case: Get user's courses."""
    
    def __init__(self, course_repository: CourseRepository):
        """Initialize use case with repository."""
        self.course_repo = course_repository
    
    async def execute(self, owner_id: str) -> List[Course]:
        """
        Get all courses for a user.
        
        Business rules:
        - Only owner can see their courses
        - Sorted by creation date (newest first)
        
        Args:
            owner_id: User ID of course owner
            
        Returns:
            List of Course entities
        """
        courses = await self.course_repo.get_by_owner(owner_id)
        return courses
