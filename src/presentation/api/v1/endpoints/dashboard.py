"""Dashboard API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import json
from pathlib import Path
from datetime import datetime, timezone

from src.core.dependencies import get_db, get_current_user
from src.infrastructure.database.models.user import UserModel
from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.lecture import LectureModel
from src.infrastructure.database.models.test import TestModel
from src.infrastructure.database.models.student_attempt import StudentAttemptModel
from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
from src.presentation.schemas.dashboard import DashboardStatsResponse, DashboardCourseData


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
DEBUG_LOG_PATH = Path("/Users/daribazar/Documents/diplom/.cursor/debug-e5243e.log")
STATUS_COMPLETED = "completed"
STATUS_APPROVED = "approved"


def _debug_log(location: str, message: str, data: dict) -> None:
    # region agent log
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
        with DEBUG_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        pass
    # endregion


async def _get_user_courses(db: AsyncSession, current_user: UserModel):
    if current_user.role == "teacher":
        result = await db.execute(select(CourseModel).where(CourseModel.owner_id == current_user.id))
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


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard statistics.
    
    Returns:
    - Total courses (teacher: owned, student: enrolled)
    - Total lectures uploaded
    - Total tests taken
    - Average score
    """
    if current_user.role == "teacher":
        # Get total courses owned by teacher
        courses_result = await db.execute(
            select(func.count(CourseModel.id)).where(
                CourseModel.owner_id == current_user.id
            )
        )
        total_courses = courses_result.scalar() or 0
        
        # Get total lectures (completed) in teacher's courses
        lectures_result = await db.execute(
            select(func.count(LectureModel.id))
            .join(CourseModel)
            .where(
                and_(
                    CourseModel.owner_id == current_user.id,
                    LectureModel.status == STATUS_COMPLETED
                )
            )
        )
        total_lectures = lectures_result.scalar() or 0
    else:
        # Get total enrolled courses for student
        courses_result = await db.execute(
            select(func.count(CourseEnrollmentModel.id)).where(
                and_(
                    CourseEnrollmentModel.student_id == current_user.id,
                    CourseEnrollmentModel.status == STATUS_APPROVED
                )
            )
        )
        total_courses = courses_result.scalar() or 0
        
        # Get total lectures in enrolled courses
        lectures_result = await db.execute(
            select(func.count(LectureModel.id))
            .join(CourseModel)
            .join(CourseEnrollmentModel, CourseModel.id == CourseEnrollmentModel.course_id)
            .where(
                and_(
                    CourseEnrollmentModel.student_id == current_user.id,
                    CourseEnrollmentModel.status == STATUS_APPROVED,
                    LectureModel.status == STATUS_COMPLETED
                )
            )
        )
        total_lectures = lectures_result.scalar() or 0
    
    # Get test statistics
    attempts_result = await db.execute(
        select(
            func.count(StudentAttemptModel.id).label('total_tests'),
            func.avg(StudentAttemptModel.percentage).label('avg_score')
        )
        .where(StudentAttemptModel.student_id == current_user.id)
    )
    test_stats = attempts_result.first()
    
    total_tests = test_stats.total_tests if test_stats else 0
    avg_score = round(test_stats.avg_score, 1) if test_stats and test_stats.avg_score else 0
    
    return DashboardStatsResponse(
        total_courses=total_courses,
        total_lectures=total_lectures,
        total_tests=total_tests,
        average_score=avg_score
    )


@router.get("/courses", response_model=list[DashboardCourseData])
async def get_dashboard_courses(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get courses with their statistics for dashboard.
    
    Returns courses with:
    - Lecture count
    - Test count
    - Average score
    
    Teacher: owned courses
    Student: enrolled courses
    """
    courses = await _get_user_courses(db, current_user)
    
    course_ids = [course.id for course in courses]
    if not course_ids:
        _debug_log(
            "src/presentation/api/v1/endpoints/dashboard.py:164",
            "No dashboard courses found",
            {"user_id": current_user.id, "role": current_user.role},
        )
        return []

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
    lectures_by_course = {
        row.course_id: row.lectures_count for row in lectures_counts_result
    }

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
                StudentAttemptModel.student_id == current_user.id,
            )
        )
        .group_by(LectureModel.course_id)
    )
    attempts_by_course = {
        row.course_id: {"test_count": row.test_count, "avg_score": row.avg_score}
        for row in attempts_stats_result
    }

    _debug_log(
        "src/presentation/api/v1/endpoints/dashboard.py:202",
        "Dashboard aggregated stats computed",
        {
            "user_id": current_user.id,
            "course_count": len(courses),
            "lecture_stat_rows": len(lectures_by_course),
            "attempt_stat_rows": len(attempts_by_course),
        },
    )

    course_data = []
    for course in courses:
        lecture_count = lectures_by_course.get(course.id, 0)
        attempt_stats = attempts_by_course.get(course.id)
        tests_count = attempt_stats["test_count"] if attempt_stats else 0
        avg_score = round(attempt_stats["avg_score"], 1) if attempt_stats and attempt_stats["avg_score"] else 0

        course_data.append(DashboardCourseData(
            id=course.id,
            name=course.name,
            code=course.code,
            semester=course.semester,
            instructor=course.instructor or "",
            color=course.color or "blue",
            lectures_uploaded=lecture_count,
            tests_completed=tests_count,
            average_score=avg_score
        ))
    
    return course_data
