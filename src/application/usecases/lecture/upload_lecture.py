"""Upload lecture use case."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.lecture import Lecture
from src.infrastructure.database.repositories.lecture_repository import LectureRepository
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.infrastructure.processing.pdf_processor import PDFProcessor
from src.domain.interfaces.storage_service import IStorageService
from src.core.exceptions import NotFoundError, UnauthorizedError
from src.core.utils import generate_id

logger = logging.getLogger(__name__)

STATUS_PENDING = "pending"


class UploadLectureUseCase:
    def __init__(
        self,
        db: AsyncSession,
        lecture_repository: LectureRepository,
        course_repository: CourseRepository,
        storage_service: IStorageService,
    ):
        self.db = db
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
        is_visible: bool = True,
    ) -> Lecture:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundError(f"Course {course_id} not found")
        if course.owner_id != user_id:
            raise UnauthorizedError("You don't own this course")

        existing = await self.lecture_repo.get_by_course_and_week(course_id, week_number)
        if existing:
            if existing.file_url:
                try:
                    await self.storage.delete(existing.file_url)
                except Exception as e:
                    logger.warning("Failed to delete previous lecture file: %s", e)
            await self.lecture_repo.delete(existing.id)
            await self.db.commit()

        file_url = await self.storage.upload(
            file_data=file_data,
            filename=f"lecture_w{week_number}_{generate_id()[:8]}.pdf",
            folder=f"courses/{course_id}/lectures",
        )

        content = ""
        try:
            content = await PDFProcessor().extract_text(file_data)
        except Exception as e:
            logger.warning("PDF text extraction failed for %s: %s", filename, e)
            content = ""

        lecture = Lecture(
            id=generate_id("lec"),
            course_id=course_id,
            week_number=week_number,
            title=title,
            file_url=file_url,
            content=content,
            status=STATUS_PENDING,
            is_visible=is_visible,
        )
        created_lecture = await self.lecture_repo.create(lecture)
        # Persist the lecture immediately so it remains visible even if AI
        # processing fails downstream.
        await self.db.commit()

        if not content:
            logger.info(
                "Skipping AI processing for lecture %s: empty content", created_lecture.id
            )
            return created_lecture

        from src.application.usecases.lecture.process_lecture import ProcessLectureUseCase
        try:
            await ProcessLectureUseCase(self.db).execute(
                lecture_id=created_lecture.id,
                user_id=user_id,
            )
        except Exception as e:
            logger.exception("AI processing failed for lecture %s: %s", created_lecture.id, e)

        # Reload to reflect any status updates from processing.
        refreshed = await self.lecture_repo.get_by_id(created_lecture.id)
        return refreshed or created_lecture
