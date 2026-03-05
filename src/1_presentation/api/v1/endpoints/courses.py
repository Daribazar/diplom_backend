"""Course management endpoints."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, CurrentUser
from src.4_infrastructure.database.repositories.course_repository import CourseRepository
from src.2_application.usecases.course.create_course import CreateCourseUseCase
from src.2_application.usecases.course.get_courses import GetCoursesUseCase
from src.2_application.usecases.course.get_course import GetCourseUseCase
from src.2_application.usecases.course.update_course import UpdateCourseUseCase
from src.2_application.usecases.course.delete_course import DeleteCourseUseCase
from src.1_presentation.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseListResponse
)
from src.core.exceptions import NotFoundError, UnauthorizedError

router = APIRouter()


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new course",
    description="Create a new course for the authenticated user"
)
async def create_course(
    course_data: CourseCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Create new course.
    
    - **name**: Course name
    - **code**: Course code (e.g., CS401)
    - **semester**: Semester (e.g., Fall 2024)
    - **instructor**: Optional instructor name
    """
    course_repo = CourseRepository(db)
    use_case = CreateCourseUseCase(course_repo)
    
    course = await use_case.execute(
        name=course_data.name,
        code=course_data.code,
        semester=course_data.semester,
        owner_id=current_user.id,
        instructor=course_data.instructor
    )
    
    return CourseResponse(
        id=course.id,
        name=course.name,
        code=course.code,
        semester=course.semester,
        instructor=course.instructor,
        owner_id=course.owner_id,
        created_at=course.created_at
    )


@router.get(
    "",
    response_model=CourseListResponse,
    summary="Get all courses",
    description="Get all courses for the authenticated user"
)
async def get_courses(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get all courses for current user."""
    course_repo = CourseRepository(db)
    use_case = GetCoursesUseCase(course_repo)
    
    courses = await use_case.execute(owner_id=current_user.id)
    
    return CourseListResponse(
        total=len(courses),
        courses=[
            CourseResponse(
                id=c.id,
                name=c.name,
                code=c.code,
                semester=c.semester,
                instructor=c.instructor,
                owner_id=c.owner_id,
                created_at=c.created_at
            )
            for c in courses
        ]
    )


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Get course by ID",
    description="Get a single course by ID (only owner can access)"
)
async def get_course(
    course_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get single course by ID."""
    course_repo = CourseRepository(db)
    use_case = GetCourseUseCase(course_repo)
    
    try:
        course = await use_case.execute(course_id, current_user.id)
        
        return CourseResponse(
            id=course.id,
            name=course.name,
            code=course.code,
            semester=course.semester,
            instructor=course.instructor,
            owner_id=course.owner_id,
            created_at=course.created_at
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Update course",
    description="Update course details (only owner can update)"
)
async def update_course(
    course_id: str,
    course_data: CourseUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Update course."""
    course_repo = CourseRepository(db)
    use_case = UpdateCourseUseCase(course_repo)
    
    try:
        course = await use_case.execute(
            course_id=course_id,
            user_id=current_user.id,
            name=course_data.name,
            code=course_data.code,
            instructor=course_data.instructor
        )
        
        return CourseResponse(
            id=course.id,
            name=course.name,
            code=course.code,
            semester=course.semester,
            instructor=course.instructor,
            owner_id=course.owner_id,
            created_at=course.created_at
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete course",
    description="Delete course and all related data (only owner can delete)"
)
async def delete_course(
    course_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Delete course."""
    course_repo = CourseRepository(db)
    use_case = DeleteCourseUseCase(course_repo)
    
    try:
        await use_case.execute(course_id, current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
