"""Shared course access helpers for API endpoints."""
from datetime import datetime, timezone
import json
from pathlib import Path

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
from src.infrastructure.database.repositories.course_repository import CourseRepository

DEBUG_LOG_PATH = Path("/Users/daribazar/Documents/diplom/.cursor/debug-e5243e.log")


def _debug_log(message: str, data: dict) -> None:
    # region agent log
    try:
        payload = {
            "sessionId": "e5243e",
            "runId": "post-fix",
            "hypothesisId": "H5",
            "location": "src/presentation/api/course_access.py:16",
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


async def has_course_access(
    db: AsyncSession,
    course_repo: CourseRepository,
    course_id: str,
    user_id: str,
    user_role: str,
) -> bool:
    """Return True when user is owner or approved enrolled student."""
    course = await course_repo.get_by_id(course_id)
    if not course:
        _debug_log("Course access denied - course missing", {"course_id": course_id, "user_id": user_id})
        return False

    if course.owner_id == user_id:
        _debug_log("Course access granted - owner", {"course_id": course_id, "user_id": user_id})
        return True

    if user_role != "student":
        _debug_log(
            "Course access denied - not owner/non-student",
            {"course_id": course_id, "user_id": user_id, "user_role": user_role},
        )
        return False

    result = await db.execute(
        select(CourseEnrollmentModel).where(
            and_(
                CourseEnrollmentModel.course_id == course_id,
                CourseEnrollmentModel.student_id == user_id,
                CourseEnrollmentModel.status == "approved",
            )
        )
    )
    is_enrolled = result.scalar_one_or_none() is not None
    _debug_log(
        "Course access checked via enrollment",
        {"course_id": course_id, "user_id": user_id, "is_enrolled": is_enrolled},
    )
    return is_enrolled
