"""Helper utilities for dashboard endpoints."""

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
from src.infrastructure.database.models.lecture import LectureModel
from src.infrastructure.database.models.student_attempt import StudentAttemptModel
from src.infrastructure.database.models.test import TestModel
from src.infrastructure.database.models.user import UserModel

DEBUG_LOG_PATH = Path("/Users/daribazar/Documents/diplom/.cursor/debug-e5243e.log")
STATUS_COMPLETED = "completed"
STATUS_APPROVED = "approved"
ROLE_TEACHER = "teacher"


def debug_log(location: str, message: str, data: dict) -> None:
    try:
        payload = {
            "sessionId": "e5243e",
            "runId": "post-fix",
            "hypothesisId": "H8",
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(datetime.now(tz=timezone.utc).timestamp() * 1000),
        }
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        return


async def get_user_courses(db: AsyncSession, current_user: UserModel):
    if current_user.role == ROLE_TEACHER:
        result = await db.execute(
            select(CourseModel).where(CourseModel.owner_id == current_user.id)
        )
        return result.scalars().all()

    result = await db.execute(
        select(CourseModel)
        .join(CourseEnrollmentModel, CourseModel.id == CourseEnrollmentModel.course_id)
        .where(
            and_(
                CourseEnrollmentModel.student_id == current_user.id,
                CourseEnrollmentModel.status == STATUS_APPROVED,
            )
        )
    )
    return result.scalars().all()


async def get_teacher_totals(db: AsyncSession, user_id: str) -> tuple[int, int]:
    courses_result = await db.execute(
        select(func.count(CourseModel.id)).where(CourseModel.owner_id == user_id)
    )
    lectures_result = await db.execute(
        select(func.count(LectureModel.id))
        .join(CourseModel)
        .where(
            and_(
                CourseModel.owner_id == user_id,
                LectureModel.status == STATUS_COMPLETED,
            )
        )
    )
    return courses_result.scalar() or 0, lectures_result.scalar() or 0


async def get_student_totals(db: AsyncSession, user_id: str) -> tuple[int, int]:
    courses_result = await db.execute(
        select(func.count(CourseEnrollmentModel.id)).where(
            and_(
                CourseEnrollmentModel.student_id == user_id,
                CourseEnrollmentModel.status == STATUS_APPROVED,
            )
        )
    )
    lectures_result = await db.execute(
        select(func.count(LectureModel.id))
        .join(CourseModel)
        .join(CourseEnrollmentModel, CourseModel.id == CourseEnrollmentModel.course_id)
        .where(
            and_(
                CourseEnrollmentModel.student_id == user_id,
                CourseEnrollmentModel.status == STATUS_APPROVED,
                LectureModel.status == STATUS_COMPLETED,
            )
        )
    )
    return courses_result.scalar() or 0, lectures_result.scalar() or 0


async def get_test_stats(db: AsyncSession, user_id: str) -> tuple[int, float]:
    attempts_result = await db.execute(
        select(
            func.count(StudentAttemptModel.id).label("total_tests"),
            func.avg(StudentAttemptModel.percentage).label("avg_score"),
        ).where(StudentAttemptModel.student_id == user_id)
    )
    test_stats = attempts_result.first()
    total_tests = test_stats.total_tests if test_stats else 0
    average_score = (
        round(test_stats.avg_score, 1) if test_stats and test_stats.avg_score else 0
    )
    return total_tests, average_score


async def get_lecture_counts_by_course(
    db: AsyncSession, course_ids: list[str]
) -> dict[str, int]:
    lectures_counts_result = await db.execute(
        select(
            LectureModel.course_id,
            func.count(LectureModel.id).label("lectures_count"),
        )
        .where(
            and_(
                LectureModel.course_id.in_(course_ids),
                LectureModel.status == STATUS_COMPLETED,
            )
        )
        .group_by(LectureModel.course_id)
    )
    return {row.course_id: row.lectures_count for row in lectures_counts_result}


async def get_attempt_stats_by_course(
    db: AsyncSession, course_ids: list[str], user_id: str
) -> dict[str, dict]:
    attempts_stats_result = await db.execute(
        select(
            LectureModel.course_id,
            func.count(StudentAttemptModel.id).label("test_count"),
            func.avg(StudentAttemptModel.percentage).label("avg_score"),
        )
        .join(TestModel, TestModel.lecture_id == LectureModel.id)
        .join(StudentAttemptModel, StudentAttemptModel.test_id == TestModel.id)
        .where(
            and_(
                LectureModel.course_id.in_(course_ids),
                StudentAttemptModel.student_id == user_id,
            )
        )
        .group_by(LectureModel.course_id)
    )
    return {
        row.course_id: {"test_count": row.test_count, "avg_score": row.avg_score}
        for row in attempts_stats_result
    }
