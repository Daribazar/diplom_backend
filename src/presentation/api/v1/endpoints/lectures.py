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

from src.application.usecases.lecture.process_lecture import ProcessLectureUseCase
from src.application.usecases.lecture.upload_lecture import UploadLectureUseCase
from src.config import settings
from src.core.dependencies import CurrentUser, get_db
from src.core.exceptions import NotFoundError, UnauthorizedError
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


async def _require_course_owner(
    course_repo: CourseRepository, course_id: str, user_id: str
):
    course = await course_repo.get_by_id(course_id)
    if not course or course.owner_id != user_id:
        raise UnauthorizedError("Хичээлийн эзэн л үйлдэл хийх эрхтэй")
    return course


def _lecture_repositories(
    db: AsyncSession,
) -> tuple[LectureRepository, CourseRepository]:
    return LectureRepository(db), CourseRepository(db)


DOMAIN_ERRORS = (NotFoundError, UnauthorizedError, ValueError, PermissionError)


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
    """Upload a PDF lecture. Replaces any existing lecture for the same week."""
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    file_data = await file.read()
    if len(file_data) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 10MB)",
        )

    lecture_repo, course_repo = _lecture_repositories(db)
    use_case = UploadLectureUseCase(db, lecture_repo, course_repo, LocalStorageService())

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
            message="Lecture uploaded and processed successfully.",
        )
    except DOMAIN_ERRORS as e:
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
    """Run AI pipeline (concepts + embeddings) on a lecture."""
    try:
        result = await ProcessLectureUseCase(db).execute(
            lecture_id=lecture_id, user_id=current_user.id
        )
        return {"message": "Lecture processed successfully", **result}
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
    """Get lecture processing status (owner only)."""
    lecture_repo, course_repo = _lecture_repositories(db)
    try:
        lecture = await _require_lecture(lecture_repo, lecture_id)
        await _require_course_owner(course_repo, lecture.course_id, current_user.id)
        return _to_lecture_status_response(lecture)
    except DOMAIN_ERRORS as e:
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
            db, course_repo, lecture.course_id, current_user.id, current_user.role
        ):
            raise UnauthorizedError("Access denied")

        if not lecture.is_visible and current_user.role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Багш энэ лекцийг нууцалсан байна",
            )

        if not lecture.file_url:
            raise NotFoundError("Lecture file not found")
        file_path = Path(settings.UPLOAD_DIR) / lecture.file_url
        if not file_path.exists():
            raise NotFoundError("Lecture file not found")

        return FileResponse(
            path=str(file_path),
            media_type="application/pdf",
            filename=f"{lecture.title}.pdf",
        )
    except DOMAIN_ERRORS as e:
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
        await _require_course_owner(course_repo, lecture.course_id, current_user.id)
        lecture.is_visible = is_visible
        return _to_lecture_response(await lecture_repo.update(lecture))
    except DOMAIN_ERRORS as e:
        raise map_common_domain_error(e)


@router.delete(
    "/{lecture_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete lecture",
    description="Delete a lecture (course owner only).",
)
async def delete_lecture(
    lecture_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Course owner can remove a wrongly uploaded lecture."""
    lecture_repo, course_repo = _lecture_repositories(db)
    try:
        lecture = await _require_lecture(lecture_repo, lecture_id)
        await _require_course_owner(course_repo, lecture.course_id, current_user.id)
        if lecture.file_url:
            try:
                await LocalStorageService().delete(lecture.file_url)
            except Exception:
                pass
        await lecture_repo.delete(lecture_id)
    except DOMAIN_ERRORS as e:
        raise map_common_domain_error(e)
