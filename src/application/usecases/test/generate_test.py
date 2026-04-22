"""Generate test use case."""

import logging
from typing import List, Optional
from sqlalchemy import select, and_

from src.domain.entities.test import Test
from src.domain.agents.test_generator_agent import (
    TestGeneratorAgent,
    QuestionType,
    Difficulty,
)
from src.infrastructure.database.repositories.test_repository import TestRepository
from src.infrastructure.database.repositories.lecture_repository import (
    LectureRepository,
)
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
from src.infrastructure.database.models.user import UserModel
from src.core.exceptions import NotFoundError, UnauthorizedError
from src.core.utils import generate_id

logger = logging.getLogger(__name__)
DEFAULT_TIME_LIMIT_MINUTES = 30
ROLE_STUDENT = "student"
STATUS_APPROVED = "approved"
STATUS_COMPLETED = "completed"
DEFAULT_QUESTION_TYPES = ["mcq", "true_false"]


class GenerateTestUseCase:
    """Use case: Generate test using AI."""

    def __init__(
        self,
        test_repository: TestRepository,
        lecture_repository: LectureRepository,
        course_repository: CourseRepository,
        test_generator: TestGeneratorAgent,
    ):
        """
        Initialize use case.

        Args:
            test_repository: Test repository
            lecture_repository: Lecture repository
            course_repository: Course repository
            test_generator: Test generator agent
        """
        self.test_repo = test_repository
        self.lecture_repo = lecture_repository
        self.course_repo = course_repository
        self.generator = test_generator

    async def _has_course_access(self, course_id: str, user_id: str) -> bool:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundError(f"Хичээл олдсонгүй: {course_id}")
        if course.owner_id == user_id:
            return True

        session = self.course_repo.session
        user_result = await session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user or user.role != ROLE_STUDENT:
            return False

        enrollment_result = await session.execute(
            select(CourseEnrollmentModel).where(
                and_(
                    CourseEnrollmentModel.course_id == course_id,
                    CourseEnrollmentModel.student_id == user_id,
                    CourseEnrollmentModel.status == STATUS_APPROVED,
                )
            )
        )
        return enrollment_result.scalar_one_or_none() is not None

    @staticmethod
    def _serialize_questions(questions) -> List[dict]:
        return [
            {
                "question_id": q.question_id,
                "type": q.type.value,
                "question_text": q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "points": q.points,
                "difficulty": q.difficulty.value,
                "bloom_level": q.bloom_level,
                "explanation": q.explanation,
            }
            for q in questions
        ]

    async def execute(
        self,
        course_id: str,
        week_number: int,
        user_id: str,
        difficulty: str = "medium",
        question_types: Optional[List[str]] = None,
        question_count: int = 10,
    ) -> Test:
        """
        Generate test for a week.

        Business rules:
        - User must own the course OR be an enrolled student
        - Lecture must be processed

        Args:
            course_id: Course ID
            week_number: Week number
            user_id: User ID
            difficulty: Difficulty level
            question_types: Question types
            question_count: Number of questions

        Returns:
            Created test

        Raises:
            NotFoundError: If course/lecture not found
            UnauthorizedError: If user doesn't have access
            ValueError: If lecture not ready
        """
        if not await self._has_course_access(course_id, user_id):
            raise UnauthorizedError("Та энэ хичээлд хандах эрхгүй байна")

        # Check lecture exists and is processed
        lecture = await self.lecture_repo.get_by_course_and_week(course_id, week_number)

        if not lecture:
            raise NotFoundError(f"{week_number}-р долоо хоногийн лекц олдсонгүй")

        if lecture.status != STATUS_COMPLETED:
            raise ValueError(f"Лекц боловсруулагдаагүй байна. Статус: {lecture.status}")

        # Parse parameters
        difficulty_enum = Difficulty(difficulty)

        if question_types is None:
            question_types = DEFAULT_QUESTION_TYPES

        question_type_enums = [QuestionType(qt) for qt in question_types]

        # Generate test (AI Agent with RAG)
        logger.info(
            "Generating test lecture_id=%s difficulty=%s types=%s count=%s",
            lecture.id,
            difficulty,
            question_types,
            question_count,
        )

        result = await self.generator.generate_test(
            lecture_ids=[lecture.id],
            difficulty=difficulty_enum,
            question_types=question_type_enums,
            question_count=question_count,
        )

        logger.info(
            "Generated test questions=%s total_points=%s",
            len(result.questions),
            result.total_points,
        )

        if not result.questions:
            raise ValueError(
                "AI асуулт үүсгэж чадсангүй. Дахин оролдоно уу."
            )

        # Create Test entity
        test = Test(
            id=generate_id("test"),
            lecture_id=lecture.id,
            created_by=user_id,
            title=f"Week {week_number} Test - {difficulty.capitalize()}",
            difficulty=difficulty,
            total_points=result.total_points,
            time_limit=DEFAULT_TIME_LIMIT_MINUTES,
            questions=self._serialize_questions(result.questions),
        )

        # Save to database
        created_test = await self.test_repo.create(test)

        return created_test
