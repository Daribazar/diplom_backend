"""Dashboard API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_current_user
from src.infrastructure.database.models.user import UserModel
from src.presentation.api.v1.endpoints.dashboard_helpers import (
    ROLE_TEACHER,
    debug_log,
    get_attempt_stats_by_course,
    get_lecture_counts_by_course,
    get_student_totals,
    get_teacher_totals,
    get_test_stats,
    get_user_courses,
)
from src.presentation.schemas.dashboard import (
    DashboardCourseData,
    DashboardStatsResponse,
)


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard statistics.

    Returns:
    - Total courses (teacher: owned, student: enrolled)
    - Total lectures uploaded
    - Total tests taken
    - Average score
    """
    if current_user.role == ROLE_TEACHER:
        total_courses, total_lectures = await get_teacher_totals(db, current_user.id)
    else:
        total_courses, total_lectures = await get_student_totals(db, current_user.id)

    total_tests, avg_score = await get_test_stats(db, current_user.id)

    return DashboardStatsResponse(
        total_courses=total_courses,
        total_lectures=total_lectures,
        total_tests=total_tests,
        average_score=avg_score,
    )


@router.get("/courses", response_model=list[DashboardCourseData])
async def get_dashboard_courses(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
    courses = await get_user_courses(db, current_user)

    course_ids = [course.id for course in courses]
    if not course_ids:
        debug_log(
            "src/presentation/api/v1/endpoints/dashboard.py:164",
            "No dashboard courses found",
            {"user_id": current_user.id, "role": current_user.role},
        )
        return []

    lectures_by_course = await get_lecture_counts_by_course(
        db,
        course_ids,
    )

    attempts_by_course = await get_attempt_stats_by_course(
        db,
        course_ids,
        current_user.id,
    )

    debug_log(
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
        avg_score = (
            round(attempt_stats["avg_score"], 1)
            if attempt_stats and attempt_stats["avg_score"]
            else 0
        )

        course_data.append(
            DashboardCourseData(
                id=course.id,
                name=course.name,
                code=course.code,
                semester=course.semester,
                instructor=course.instructor or "",
                color=course.color or "blue",
                lectures_uploaded=lecture_count,
                tests_completed=tests_count,
                average_score=avg_score,
            )
        )

    return course_data
