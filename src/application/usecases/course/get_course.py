"""Get single course use case."""

from src.domain.entities.course import Course
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.core.exceptions import NotFoundError, UnauthorizedError


class GetCourseUseCase:
    """Use case: Get single course."""

    def __init__(self, course_repository: CourseRepository):
        """Initialize use case with repository."""
        self.course_repo = course_repository

    async def execute(self, course_id: str, user_id: str) -> Course:
        """
        Get course by ID.

        Business rules:
        - Course must exist
        - Only owner can access

        Args:
            course_id: Course ID
            user_id: User ID requesting access

        Returns:
            Course entity

        Raises:
            NotFoundError: If course doesn't exist
            UnauthorizedError: If user is not the owner
        """
        course = await self.course_repo.get_by_id(course_id)

        if not course:
            raise NotFoundError(f"Course {course_id} not found")

        # Authorization check
        if course.owner_id != user_id:
            raise UnauthorizedError("You don't have access to this course")

        return course
