"""Test generation endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, CurrentUser
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.infrastructure.database.repositories.embedding_repository import (
    EmbeddingRepository,
)
from src.infrastructure.database.repositories.lecture_repository import (
    LectureRepository,
)
from src.infrastructure.database.repositories.test_repository import TestRepository
from src.infrastructure.external.llm.llm_factory import LLMFactory
from src.application.usecases.test.generate_test import GenerateTestUseCase
from src.domain.services.chunking.semantic_chunker import SemanticChunker
from src.domain.services.embedding.embedding_service import EmbeddingService
from src.domain.agents.test_generator_agent import TestGeneratorAgent
from src.domain.memory.context_retriever import ContextRetriever
from src.domain.memory.memory_manager import MemoryManager
from src.core.exceptions import NotFoundError, UnauthorizedError
from src.presentation.api.course_access import has_course_access
from src.presentation.api.http_errors import map_common_domain_error
from src.presentation.schemas.test import (
    QuestionResponse,
    TestGenerateRequest,
    TestListResponse,
    TestResponse,
)

router = APIRouter()
ROLE_STUDENT = "student"


def _to_test_response(test) -> TestResponse:
    return TestResponse(
        id=test.id,
        lecture_id=test.lecture_id,
        title=test.title,
        difficulty=test.difficulty,
        total_points=test.total_points,
        time_limit=test.time_limit,
        questions=[QuestionResponse(**q) for q in test.questions],
        created_at=test.created_at,
    )


def _build_test_generation_use_case(db: AsyncSession) -> GenerateTestUseCase:
    test_repo = TestRepository(db)
    lecture_repo = LectureRepository(db)
    course_repo = CourseRepository(db)
    embedding_repo = EmbeddingRepository(db)

    llm = LLMFactory.create_default_adapter()
    embedding_adapter = LLMFactory.create_embedding_adapter()
    chunker = SemanticChunker(chunk_size=1000, overlap=200)
    embedding_service = EmbeddingService(embedding_adapter)
    memory_manager = MemoryManager(
        chunker=chunker,
        embedding_service=embedding_service,
        embedding_repo=embedding_repo,
    )
    context_retriever = ContextRetriever(memory_manager)
    test_generator = TestGeneratorAgent(llm, context_retriever)

    return GenerateTestUseCase(test_repo, lecture_repo, course_repo, test_generator)


async def _require_lecture_access(
    db: AsyncSession,
    lecture_repo: LectureRepository,
    course_repo: CourseRepository,
    lecture_id: str,
    current_user: CurrentUser,
):
    lecture = await lecture_repo.get_by_id(lecture_id)
    if not lecture:
        raise NotFoundError("Лекц олдсонгүй")
    if not await has_course_access(
        db,
        course_repo,
        lecture.course_id,
        current_user.id,
        current_user.role,
    ):
        raise UnauthorizedError("Хандах эрхгүй байна")
    return lecture


@router.post(
    "/generate",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI test",
    description="Generate test questions using AI based on lecture content",
)
async def generate_test(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    course_id: str = Query(..., description="Course ID"),
    request: TestGenerateRequest = ...,
):
    """
    Generate AI test for a week.

    - **course_id**: Course ID
    - **week_number**: Week number (1-16)
    - **difficulty**: easy, medium, hard
    - **question_types**: List of question types (mcq, true_false, essay)
    - **question_count**: Number of questions (5-20)
    """
    use_case = _build_test_generation_use_case(db)
    try:
        test = await use_case.execute(
            course_id=course_id,
            week_number=request.week_number,
            user_id=current_user.id,
            difficulty=request.difficulty,
            question_types=request.question_types,
            question_count=request.question_count,
        )
        return _to_test_response(test)
    except (NotFoundError, UnauthorizedError, ValueError, PermissionError) as e:
        raise map_common_domain_error(e)


@router.get(
    "/{test_id}",
    response_model=TestResponse,
    summary="Get test by ID",
    description="Retrieve a specific test (owner or enrolled students)",
)
async def get_test(
    test_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get test by ID."""
    test_repo = TestRepository(db)
    course_repo = CourseRepository(db)
    lecture_repo = LectureRepository(db)

    try:
        test = await test_repo.get_by_id(test_id)
        if not test:
            raise NotFoundError("Тест олдсонгүй")
        await _require_lecture_access(
            db,
            lecture_repo,
            course_repo,
            test.lecture_id,
            current_user,
        )
        return _to_test_response(test)
    except (NotFoundError, UnauthorizedError, ValueError, PermissionError) as e:
        raise map_common_domain_error(e)


@router.get(
    "/lecture/{lecture_id}",
    response_model=TestListResponse,
    summary="Get tests for lecture",
    description="Get all tests for a specific lecture (owner or enrolled students)",
)
async def get_lecture_tests(
    lecture_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get all tests for a lecture."""
    test_repo = TestRepository(db)
    lecture_repo = LectureRepository(db)
    course_repo = CourseRepository(db)

    try:
        await _require_lecture_access(
            db,
            lecture_repo,
            course_repo,
            lecture_id,
            current_user,
        )
        tests = await test_repo.get_by_lecture(lecture_id)
        if current_user.role == ROLE_STUDENT:
            tests = [t for t in tests if t.created_by == current_user.id]
        return TestListResponse(
            total=len(tests),
            tests=[_to_test_response(t) for t in tests],
        )
    except (NotFoundError, UnauthorizedError, ValueError, PermissionError) as e:
        raise map_common_domain_error(e)
