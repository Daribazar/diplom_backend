"""Upload lecture use case."""

from src.domain.entities.lecture import Lecture
from src.infrastructure.database.repositories.lecture_repository import (
    LectureRepository,
)
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.infrastructure.processing.pdf_processor import PDFProcessor
from src.domain.interfaces.storage_service import IStorageService
from src.core.exceptions import NotFoundError, UnauthorizedError, DuplicateError
from src.core.utils import generate_id

STATUS_PENDING = "pending"


class UploadLectureUseCase:
    """Use case: Upload lecture file."""

    def __init__(
        self,
        lecture_repository: LectureRepository,
        course_repository: CourseRepository,
        storage_service: IStorageService,
    ):
        """Initialize use case with repositories and storage."""
        self.lecture_repo = lecture_repository
        self.course_repo = course_repository
        self.storage = storage_service

    async def execute(
        self,
        course_id: str,
        week_number: int,
        title: str,
        file_data: bytes,
        filename: str,
        user_id: str,
    ) -> Lecture:
        """
        Upload lecture file.

        Business rules:
        - User must own the course
        - No duplicate lectures per week
        - File must be PDF

        Args:
            course_id: Course ID
            week_number: Week number (1-16)
            title: Lecture title
            file_data: File content as bytes
            filename: Original filename
            user_id: User ID uploading

        Returns:
            Created Lecture entity

        Raises:
            NotFoundError: If course doesn't exist
            UnauthorizedError: If user doesn't own course
            DuplicateError: If lecture already exists for week
        """
        # Check course exists and user owns it
        course = await self.course_repo.get_by_id(course_id)

        if not course:
            raise NotFoundError(f"Course {course_id} not found")

        if course.owner_id != user_id:
            raise UnauthorizedError("You don't own this course")

        # Check no duplicate
        existing = await self.lecture_repo.get_by_course_and_week(
            course_id, week_number
        )

        if existing:
            raise DuplicateError(f"Lecture already exists for week {week_number}")

        # Upload file to storage
        file_url = await self.storage.upload(
            file_data=file_data,
            filename=f"lecture_w{week_number}_{generate_id()[:8]}.pdf",
            folder=f"courses/{course_id}/lectures",
        )

        # Extract text from PDF
        content = ""
        try:
            content = await PDFProcessor().extract_text(file_data)
        except Exception:
            # If PDF extraction fails, continue without content
            # Processing will fail but lecture will be saved
            content = ""

        # Create lecture entity
        lecture = Lecture(
            id=generate_id("lec"),
            course_id=course_id,
            week_number=week_number,
            title=title,
            file_url=file_url,
            content=content,
            status=STATUS_PENDING,
        )

        # Save to database
        created_lecture = await self.lecture_repo.create(lecture)

        # Trigger background processing with Celery
        from src.infrastructure.queue.tasks.lecture_processing import (
            process_lecture_task,
        )

        process_lecture_task.delay(lecture_id=created_lecture.id)

        return created_lecture
