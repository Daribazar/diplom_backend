"""Update course use case."""

from typing import Optional
from src.domain.entities.course import Course
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.core.exceptions import NotFoundError, UnauthorizedError


class UpdateCourseUseCase:
    """Use case: Update course."""

    def __init__(self, course_repository: CourseRepository):
        """Initialize use case with repository."""
        self.course_repo = course_repository

    async def execute(
        self,
        course_id: str,
        user_id: str,
        name: Optional[str] = None,
        code: Optional[str] = None,
        instructor: Optional[str] = None,
    ) -> Course:
        """
        Update course.

        Business rules:
        - Course must exist
        - Only owner can update
        - At least one field must be provided

        Args:
            course_id: Course ID
            user_id: User ID requesting update
            name: Optional new name
            code: Optional new code
            instructor: Optional new instructor

        Returns:
            Updated Course entity

        Raises:
            NotFoundError: If course doesn't exist
            UnauthorizedError: If user is not the owner
        """
        # Get existing course
        course = await self.course_repo.get_by_id(course_id)

        if not course:
            raise NotFoundError(f"Course {course_id} not found")

        # Authorization
        if course.owner_id != user_id:
            raise UnauthorizedError("You don't have permission to update this course")

        # Update fields (domain logic)
        if name:
            course.name = name
        if code:
            course.code = code
        if instructor is not None:
            course.update_instructor(instructor)

        # Persist changes
        updated_course = await self.course_repo.update(course)

        return updated_course
