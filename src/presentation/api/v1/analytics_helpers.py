"""Helper utilities for analytics endpoints."""

from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
from src.infrastructure.database.models.lecture import LectureModel
from src.infrastructure.database.models.student_attempt import StudentAttemptModel
from src.infrastructure.database.models.test import TestModel
from src.presentation.schemas.analytics import AnalyticsOverviewResponse

ROLE_TEACHER = "teacher"
STATUS_APPROVED = "approved"
DEFAULT_TIME_MINUTES = 21
DEFAULT_CHANGE_SCORE = 3.2
DEFAULT_CHANGE_TESTS = 2
DEFAULT_CHANGE_TIME = -2


def attempts_base_query(user_id: str):
    return select(StudentAttemptModel).where(StudentAttemptModel.student_id == user_id)


def with_optional_course_filter(query, course_id: Optional[str]):
    if not course_id:
        return query
    return (
        query.join(TestModel)
        .join(LectureModel)
        .where(LectureModel.course_id == course_id)
    )


def round_score(value) -> float:
    return round(value, 1) if value else 0


def empty_overview() -> AnalyticsOverviewResponse:
    return AnalyticsOverviewResponse(
        total_score_average=0,
        total_tests=0,
        average_time_minutes=0,
        highest_score=0,
        highest_score_course=None,
        score_change=0,
        tests_change=0,
        time_change=0,
    )


async def get_course_code_for_attempt(
    db: AsyncSession,
    attempt: Optional[StudentAttemptModel],
) -> Optional[str]:
    if not attempt:
        return None

    test_result = await db.execute(
        select(TestModel).where(TestModel.id == attempt.test_id)
    )
    test = test_result.scalar_one_or_none()
    if not test:
        return None

    lecture_result = await db.execute(
        select(LectureModel).where(LectureModel.id == test.lecture_id)
    )
    lecture = lecture_result.scalar_one_or_none()
    if not lecture:
        return None

    course_result = await db.execute(
        select(CourseModel).where(CourseModel.id == lecture.course_id)
    )
    course = course_result.scalar_one_or_none()
    return course.code if course else None


def extract_topic_name(title: str, key_concepts) -> str:
    if key_concepts and isinstance(key_concepts, list) and len(key_concepts) > 0:
        return key_concepts[0]
    return title


def student_course_filter(user_id: str):
    return CourseModel.id.in_(
        select(CourseEnrollmentModel.course_id).where(
            and_(
                CourseEnrollmentModel.student_id == user_id,
                CourseEnrollmentModel.status == STATUS_APPROVED,
            )
        )
    )
