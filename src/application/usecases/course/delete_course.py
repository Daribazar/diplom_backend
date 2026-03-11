"""Delete course use case."""
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.core.exceptions import NotFoundError, UnauthorizedError


class DeleteCourseUseCase:
    """Use case: Delete course."""
    
    def __init__(self, course_repository: CourseRepository):
        """Initialize use case with repository."""
        self.course_repo = course_repository
    
    async def execute(self, course_id: str, user_id: str) -> bool:
        """
        Delete course.
        
        Business rules:
        - Course must exist
        - Only owner can delete
        - Cascade delete: all lectures, tests, attempts
        
        Args:
            course_id: Course ID
            user_id: User ID requesting deletion
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If course doesn't exist
            UnauthorizedError: If user is not the owner
        """
        # Get course
        course = await self.course_repo.get_by_id(course_id)
        
        if not course:
            raise NotFoundError(f"Course {course_id} not found")
        
        # Authorization
        if course.owner_id != user_id:
            raise UnauthorizedError("You don't have permission to delete this course")
        
        # Delete (cascade handled by database)
        deleted = await self.course_repo.delete(course_id)
        
        return deleted
