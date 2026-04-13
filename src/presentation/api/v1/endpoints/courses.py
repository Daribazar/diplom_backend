"""Course management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.usecases.course.create_course import CreateCourseUseCase
from src.application.usecases.course.delete_course import DeleteCourseUseCase
from src.application.usecases.course.get_courses import GetCoursesUseCase
from src.application.usecases.course.update_course import UpdateCourseUseCase
from src.core.dependencies import CurrentUser, get_db
from src.core.exceptions import NotFoundError, UnauthorizedError
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.presentation.schemas.course import (
    CourseCreate,
    CourseListResponse,
    CourseResponse,
    CourseUpdate,
)
from src.presentation.api.course_access import has_course_access
from src.presentation.api.http_errors import map_common_domain_error

router = APIRouter()
ROLE_TEACHER = "teacher"
STATUS_APPROVED = "approved"


def _to_course_response(course) -> CourseResponse:
    return CourseResponse(
        id=course.id,
        name=course.name,
        code=course.code,
        semester=course.semester,
        instructor=course.instructor,
        color=course.color,
        owner_id=course.owner_id,
        created_at=course.created_at,
    )


def _course_repository(db: AsyncSession) -> CourseRepository:
    return CourseRepository(db)


def _to_course_list_response(courses) -> CourseListResponse:
    return CourseListResponse(
        total=len(courses),
        courses=[_to_course_response(c) for c in courses],
    )


async def _get_student_courses(db: AsyncSession, student_id: str):
    from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
    from src.infrastructure.database.models.course import CourseModel
    from src.domain.entities.course import Course

    enrollments_result = await db.execute(
        select(CourseModel)
        .join(CourseEnrollmentModel, CourseModel.id == CourseEnrollmentModel.course_id)
        .where(
            CourseEnrollmentModel.student_id == student_id,
            CourseEnrollmentModel.status == STATUS_APPROVED,
        )
    )
    rows = enrollments_result.scalars().all()
    return [
        Course(
            id=course.id,
            name=course.name,
            code=course.code,
            semester=course.semester,
            instructor=course.instructor,
            color=course.color,
            owner_id=course.owner_id,
            created_at=course.created_at,
        )
        for course in rows
    ]


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new course",
    description="Create a new course for the authenticated user",
)
async def create_course(
    course_data: CourseCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Create new course.

    - **name**: Course name
    - **code**: Course code (e.g., CS401)
    - **semester**: Semester (e.g., Fall 2024)
    - **instructor**: Optional instructor name
    """
    course_repo = _course_repository(db)
    use_case = CreateCourseUseCase(course_repo)
    course = await use_case.execute(
        name=course_data.name,
        code=course_data.code,
        semester=course_data.semester,
        owner_id=current_user.id,
        instructor=course_data.instructor,
        color=course_data.color,
    )

    return _to_course_response(course)


@router.get(
    "",
    response_model=CourseListResponse,
    summary="Get all courses",
    description="Get all courses for the authenticated user (teacher: owned courses, student: enrolled courses)",
)
async def get_courses(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get all courses for current user."""
    course_repo = _course_repository(db)

    if current_user.role == ROLE_TEACHER:
        # Teachers see their own courses
        use_case = GetCoursesUseCase(course_repo)
        courses = await use_case.execute(owner_id=current_user.id)
    else:
        courses = await _get_student_courses(db, current_user.id)

    return _to_course_list_response(courses)


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Get course by ID",
    description="Get a single course by ID (owner or enrolled students can access)",
)
async def get_course(
    course_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get single course by ID."""
    course_repo = _course_repository(db)

    try:
        course = await course_repo.get_by_id(course_id)
        if not course:
            raise NotFoundError("Course not found")

        if not await has_course_access(
            db,
            course_repo,
            course_id,
            current_user.id,
            current_user.role,
        ):
            raise UnauthorizedError("You don't have access to this course")

        return _to_course_response(course)
    except (NotFoundError, UnauthorizedError, PermissionError, ValueError) as e:
        raise map_common_domain_error(e)


@router.patch(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Update course",
    description="Update course details (only owner can update)",
)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update course."""
    course_repo = _course_repository(db)
    use_case = UpdateCourseUseCase(course_repo)

    try:
        course = await use_case.execute(
            course_id=course_id,
            user_id=current_user.id,
            name=course_data.name,
            code=course_data.code,
            instructor=course_data.instructor,
        )

        return _to_course_response(course)
    except (NotFoundError, UnauthorizedError, PermissionError, ValueError) as e:
        raise map_common_domain_error(e)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete course",
    description="Delete course and all related data (only owner can delete)",
)
async def delete_course(
    course_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete course."""
    course_repo = _course_repository(db)
    use_case = DeleteCourseUseCase(course_repo)

    try:
        await use_case.execute(course_id, current_user.id)
    except (NotFoundError, UnauthorizedError, PermissionError, ValueError) as e:
        raise map_common_domain_error(e)
