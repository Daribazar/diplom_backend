"""Create course use case."""
import uuid
from src.3_domain.entities.course import Course
from src.4_infrastructure.database.repositories.course_repository import CourseRepository


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
        instructor: str = None
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
            
        Returns:
            Created Course entity
        """
        # Create domain entity
        course = Course(
            id=f"course_{uuid.uuid4().hex[:12]}",
            name=name,
            code=code,
            semester=semester,
            owner_id=owner_id,
            instructor=instructor
        )
        
        # Persist to database
        created_course = await self.course_repo.create(course)
        
        return created_course
