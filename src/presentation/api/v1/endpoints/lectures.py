"""Lecture management endpoints."""

from pathlib import Path
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.usecases.lecture.upload_lecture import UploadLectureUseCase
from src.config import settings
from src.core.dependencies import CurrentUser, get_db
from src.core.exceptions import DuplicateError, NotFoundError, UnauthorizedError
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.infrastructure.database.repositories.lecture_repository import (
    LectureRepository,
)
from src.infrastructure.external.storage.local_storage import LocalStorageService
from src.presentation.api.course_access import has_course_access
from src.presentation.api.http_errors import map_common_domain_error
from src.presentation.schemas.lecture import (
    LectureListResponse,
    LectureProcessResponse,
    LectureResponse,
    LectureStatusResponse,
    LectureUploadResponse,
)

router = APIRouter()
MAX_WEEKS = 16
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
STATUS_COMPLETED = "completed"


async def _require_lecture(lecture_repo: LectureRepository, lecture_id: str):
    lecture = await lecture_repo.get_by_id(lecture_id)
    if not lecture:
        raise NotFoundError("Лекц олдсонгүй")
    return lecture


def _require_file_path(lecture, file_path: Path) -> None:
    if not lecture.file_url or not file_path.exists():
        raise NotFoundError("Lecture file not found")


def _lecture_repositories(
    db: AsyncSession,
) -> tuple[LectureRepository, CourseRepository]:
    return LectureRepository(db), CourseRepository(db)


def _to_lecture_response(lecture) -> LectureResponse:
    return LectureResponse(
        id=lecture.id,
        course_id=lecture.course_id,
        week_number=lecture.week_number,
        title=lecture.title,
        status=lecture.status,
        key_concepts=lecture.key_concepts,
        is_visible=lecture.is_visible,
        created_at=lecture.created_at,
    )


def _to_lecture_status_response(lecture) -> dict:
    return {
        "lecture_id": lecture.id,
        "title": lecture.title,
        "status": lecture.status,
        "key_concepts": (
            lecture.key_concepts if lecture.status == STATUS_COMPLETED else []
        ),
        "created_at": lecture.created_at.isoformat() if lecture.created_at else None,
        "processed_at": (
            lecture.processed_at.isoformat() if lecture.processed_at else None
        ),
    }


@router.post(
    "/upload",
    response_model=LectureUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload lecture file",
    description="Upload a PDF lecture file for a course",
)
async def upload_lecture(
    course_id: Annotated[str, Form()],
    week_number: Annotated[int, Form(ge=1, le=MAX_WEEKS)],
    title: Annotated[str, Form(min_length=1, max_length=200)],
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    is_visible: Annotated[bool, Form()] = True,
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
            detail="Only PDF files are supported",
        )

    # Read file data
    file_data = await file.read()

    # Check file size (10MB max)
    if len(file_data) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 10MB)",
        )

    # Execute use case
    lecture_repo, course_repo = _lecture_repositories(db)
    storage = LocalStorageService()

    use_case = UploadLectureUseCase(
        lecture_repo,
        course_repo,
        storage,
    )

    try:
        lecture = await use_case.execute(
            course_id=course_id,
            week_number=week_number,
            title=title,
            file_data=file_data,
            filename=file.filename,
            user_id=current_user.id,
            is_visible=is_visible,
        )

        return LectureUploadResponse(
            id=lecture.id,
            course_id=lecture.course_id,
            week_number=lecture.week_number,
            title=lecture.title,
            status=lecture.status,
            is_visible=lecture.is_visible,
            message="Lecture uploaded successfully. Processing in background.",
            estimated_time="2-3 minutes",
        )

    except (
        NotFoundError,
        UnauthorizedError,
        DuplicateError,
        ValueError,
        PermissionError,
    ) as e:
        raise map_common_domain_error(e)


@router.get("/course/{course_id}", response_model=LectureListResponse)
async def get_course_lectures(
    course_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get all lectures for a course."""
    lecture_repo, course_repo = _lecture_repositories(db)

    if not await has_course_access(
        db,
        course_repo,
        course_id,
        current_user.id,
        current_user.role,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    lectures = await lecture_repo.get_by_course(course_id)

    return LectureListResponse(
        total=len(lectures),
        lectures=[_to_lecture_response(lecture) for lecture in lectures],
    )


@router.post(
    "/{lecture_id}/process",
    response_model=LectureProcessResponse,
    summary="Process lecture",
    description="Process lecture with AI agents (extract concepts, create embeddings)",
)
async def process_lecture(
    lecture_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
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
        result = await use_case.execute(lecture_id=lecture_id, user_id=current_user.id)
        return {
            "message": "Lecture processed successfully",
            "lecture_id": result["lecture_id"],
            "key_concepts": result["key_concepts"],
            "chunks_created": result["chunks_created"],
            "llm_usage": result["llm_usage"],
        }
    except Exception as e:
        raise map_common_domain_error(e)


@router.get(
    "/{lecture_id}/status",
    response_model=LectureStatusResponse,
    summary="Get lecture processing status",
    description="Check the processing status of a lecture",
)
async def get_lecture_status(
    lecture_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """
    Get lecture processing status.

    Returns:
    - pending: Waiting for processing
    - processing: Currently being processed
    - completed: Processing finished successfully
    - failed: Processing failed
    """
    lecture_repo, course_repo = _lecture_repositories(db)

    try:
        lecture = await _require_lecture(lecture_repo, lecture_id)

        course = await course_repo.get_by_id(lecture.course_id)
        if not course or course.owner_id != current_user.id:
            raise UnauthorizedError("Access denied")

        return _to_lecture_status_response(lecture)
    except (NotFoundError, UnauthorizedError, ValueError, PermissionError) as e:
        raise map_common_domain_error(e)


@router.get("/{lecture_id}/file")
async def get_lecture_file(
    lecture_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get lecture PDF file."""
    lecture_repo, course_repo = _lecture_repositories(db)

    try:
        lecture = await _require_lecture(lecture_repo, lecture_id)

        if not await has_course_access(
            db,
            course_repo,
            lecture.course_id,
            current_user.id,
            current_user.role,
        ):
            raise UnauthorizedError("Access denied")

        if not lecture.is_visible and current_user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Багш энэ лекцийг нууцалсан байна",
            )

        file_path = (
            Path(settings.UPLOAD_DIR) / lecture.file_url if lecture.file_url else Path()
        )
        _require_file_path(lecture, file_path)

        return FileResponse(
            path=str(file_path),
            media_type="application/pdf",
            filename=f"{lecture.title}.pdf",
        )
    except (NotFoundError, UnauthorizedError, ValueError, PermissionError) as e:
        raise map_common_domain_error(e)


@router.patch(
    "/{lecture_id}/visibility",
    response_model=LectureResponse,
    summary="Toggle lecture visibility",
    description="Teacher (course owner) can show or hide a lecture from students.",
)
async def update_lecture_visibility(
    lecture_id: str,
    current_user: CurrentUser,
    is_visible: Annotated[bool, Body(embed=True)],
    db: AsyncSession = Depends(get_db),
):
    """Allow the course owner to mark a lecture visible/hidden for students."""
    lecture_repo, course_repo = _lecture_repositories(db)

    try:
        lecture = await _require_lecture(lecture_repo, lecture_id)
        course = await course_repo.get_by_id(lecture.course_id)
        if not course or course.owner_id != current_user.id:
            raise UnauthorizedError("Only the course owner can change visibility")

        lecture.is_visible = is_visible
        updated = await lecture_repo.update(lecture)
        return _to_lecture_response(updated)
    except (NotFoundError, UnauthorizedError, ValueError, PermissionError) as e:
        raise map_common_domain_error(e)
