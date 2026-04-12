"""Lecture management endpoints."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, CurrentUser
from src.infrastructure.database.repositories.lecture_repository import LectureRepository
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.infrastructure.external.storage.local_storage import LocalStorageService
from src.application.usecases.lecture.upload_lecture import UploadLectureUseCase
from src.presentation.schemas.lecture import (
    LectureUploadResponse,
    LectureResponse,
    LectureListResponse
)
from src.core.exceptions import NotFoundError, UnauthorizedError, DuplicateError

router = APIRouter()


@router.post(
    "/upload",
    response_model=LectureUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload lecture file",
    description="Upload a PDF lecture file for a course"
)
async def upload_lecture(
    course_id: Annotated[str, Form()],
    week_number: Annotated[int, Form(ge=1, le=16)],
    title: Annotated[str, Form(min_length=1, max_length=200)],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...)
):
    """
    Upload lecture file (PDF).
    
    - **course_id**: Course identifier
    - **week_number**: Week number (1-16)
    - **title**: Lecture title
    - **file**: PDF file
    """
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )
    
    # Read file data
    file_data = await file.read()
    
    # Check file size (10MB max)
    if len(file_data) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 10MB)"
        )
    
    # Execute use case
    lecture_repo = LectureRepository(db)
    course_repo = CourseRepository(db)
    storage = LocalStorageService()
    
    use_case = UploadLectureUseCase(
        lecture_repo,
        course_repo,
        storage
    )
    
    try:
        lecture = await use_case.execute(
            course_id=course_id,
            week_number=week_number,
            title=title,
            file_data=file_data,
            filename=file.filename,
            user_id=current_user.id
        )
        
        return LectureUploadResponse(
            id=lecture.id,
            course_id=lecture.course_id,
            week_number=lecture.week_number,
            title=lecture.title,
            status=lecture.status,
            message="Lecture uploaded successfully. Processing in background.",
            estimated_time="2-3 minutes"
        )
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except DuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get(
    "/course/{course_id}",
    response_model=LectureListResponse,
    summary="Get course lectures",
    description="Get all lectures for a course (owner or enrolled students)"
)
async def get_course_lectures(
    course_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get all lectures for a course."""
    from sqlalchemy import select, and_
    from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
    
    lecture_repo = LectureRepository(db)
    course_repo = CourseRepository(db)
    
    # Check course access
    course = await course_repo.get_by_id(course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Хичээл олдсонгүй"
        )
    
    # Check if user is owner or enrolled student
    has_access = course.owner_id == current_user.id
    
    if not has_access and current_user.role == "student":
        # Check enrollment
        enrollment_result = await db.execute(
            select(CourseEnrollmentModel).where(
                and_(
                    CourseEnrollmentModel.course_id == course_id,
                    CourseEnrollmentModel.student_id == current_user.id,
                    CourseEnrollmentModel.status == "approved"
                )
            )
        )
        enrollment = enrollment_result.scalar_one_or_none()
        has_access = enrollment is not None
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this course"
        )
    
    # Get lectures
    lectures = await lecture_repo.get_by_course(course_id)
    
    return LectureListResponse(
        total=len(lectures),
        lectures=[
            LectureResponse(
                id=l.id,
                course_id=l.course_id,
                week_number=l.week_number,
                title=l.title,
                status=l.status,
                key_concepts=l.key_concepts,
                created_at=l.created_at
            )
            for l in lectures
        ]
    )


@router.post(
    "/{lecture_id}/process",
    response_model=dict,
    summary="Process lecture",
    description="Process lecture with AI agents (extract concepts, create embeddings)"
)
async def process_lecture(
    lecture_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Process lecture through AI pipeline.
    
    - Extracts key concepts
    - Creates embeddings for RAG
    - Updates lecture status
    """
    from src.application.usecases.lecture.process_lecture import ProcessLectureUseCase
    
    use_case = ProcessLectureUseCase(db)
    
    try:
        result = await use_case.execute(
            lecture_id=lecture_id,
            user_id=current_user.id
        )
        
        return {
            "message": "Lecture processed successfully",
            "lecture_id": result["lecture_id"],
            "key_concepts": result["key_concepts"],
            "chunks_created": result["chunks_created"],
            "llm_usage": result["llm_usage"]
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.get(
    "/{lecture_id}/status",
    response_model=dict,
    summary="Get lecture processing status",
    description="Check the processing status of a lecture"
)
async def get_lecture_status(
    lecture_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Get lecture processing status.
    
    Returns:
    - pending: Waiting for processing
    - processing: Currently being processed
    - completed: Processing finished successfully
    - failed: Processing failed
    """
    lecture_repo = LectureRepository(db)
    course_repo = CourseRepository(db)
    
    # Get lecture
    lecture = await lecture_repo.get_by_id(lecture_id)
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лекц олдсонгүй"
        )
    
    # Check course access
    course = await course_repo.get_by_id(lecture.course_id)
    if not course or course.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return {
        "lecture_id": lecture.id,
        "title": lecture.title,
        "status": lecture.status,
        "key_concepts": lecture.key_concepts if lecture.status == "completed" else [],
        "created_at": lecture.created_at.isoformat() if lecture.created_at else None,
        "processed_at": lecture.processed_at.isoformat() if lecture.processed_at else None
    }
