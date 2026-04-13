"""Create course use case."""
from src.domain.entities.course import Course
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.core.utils import generate_id


class CreateCourseUseCase:
    """Use case: Create new course."""
    
    def __init__(self, course_repository: CourseRepository):
        """Initialize use case with repository."""
        self.course_repo = course_repository
    
    async def execute(
        self,
        name: str,
        code: str,
        semester: str,
        owner_id: str,
        instructor: str = None,
        color: str = "indigo"
    ) -> Course:
        """
        Create new course.
        
        Business rules:
        - Course must have unique code per owner per semester
        - Owner must be authenticated user
        
        Args:
            name: Course name
            code: Course code (e.g., CS401)
            semester: Semester (e.g., Fall 2024)
            owner_id: User ID of course owner
            instructor: Optional instructor name
            color: Course color for UI display
            
        Returns:
            Created Course entity
        """
        # Create domain entity
        course = Course(
            id=generate_id("course"),
            name=name,
            code=code,
            semester=semester,
            owner_id=owner_id,
            instructor=instructor,
            color=color
        )
        
        # Persist to database
        created_course = await self.course_repo.create(course)
        
        return created_course
