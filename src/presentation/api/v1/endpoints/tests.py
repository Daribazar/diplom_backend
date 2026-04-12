"""Test generation endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, CurrentUser
from src.infrastructure.database.repositories.test_repository import TestRepository
from src.infrastructure.database.repositories.lecture_repository import LectureRepository
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.infrastructure.database.repositories.embedding_repository import EmbeddingRepository
from src.infrastructure.external.llm.llm_factory import LLMFactory
from src.domain.agents.test_generator_agent import TestGeneratorAgent
from src.domain.services.chunking.semantic_chunker import SemanticChunker
from src.domain.services.embedding.embedding_service import EmbeddingService
from src.domain.memory.memory_manager import MemoryManager
from src.domain.memory.context_retriever import ContextRetriever
from src.application.usecases.test.generate_test import GenerateTestUseCase
from src.presentation.schemas.test import (
    TestGenerateRequest,
    TestResponse,
    QuestionResponse,
    TestListResponse
)
from src.core.exceptions import NotFoundError, UnauthorizedError

router = APIRouter()


@router.post(
    "/generate",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI test",
    description="Generate test questions using AI based on lecture content"
)
async def generate_test(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    course_id: str = Query(..., description="Course ID"),
    request: TestGenerateRequest = ...
):
    """
    Generate AI test for a week.
    
    - **course_id**: Course ID
    - **week_number**: Week number (1-16)
    - **difficulty**: easy, medium, hard
    - **question_types**: List of question types (mcq, true_false, essay)
    - **question_count**: Number of questions (5-20)
    """
    # Initialize repositories
    test_repo = TestRepository(db)
    lecture_repo = LectureRepository(db)
    course_repo = CourseRepository(db)
    embedding_repo = EmbeddingRepository(db)
    
    # Initialize LLM and services
    llm = LLMFactory.create_default_adapter()
    embedding_adapter = LLMFactory.create_embedding_adapter()
    
    chunker = SemanticChunker(chunk_size=1000, overlap=200)
    embedding_service = EmbeddingService(embedding_adapter)
    
    # Initialize memory and context retriever
    memory_manager = MemoryManager(
        chunker=chunker,
        embedding_service=embedding_service,
        embedding_repo=embedding_repo
    )
    context_retriever = ContextRetriever(memory_manager)
    
    # Initialize test generator agent
    test_generator = TestGeneratorAgent(llm, context_retriever)
    
    # Initialize use case
    use_case = GenerateTestUseCase(
        test_repo,
        lecture_repo,
        course_repo,
        test_generator
    )
    
    try:
        test = await use_case.execute(
            course_id=course_id,
            week_number=request.week_number,
            user_id=current_user.id,
            difficulty=request.difficulty,
            question_types=request.question_types,
            question_count=request.question_count
        )
        
        return TestResponse(
            id=test.id,
            lecture_id=test.lecture_id,
            title=test.title,
            difficulty=test.difficulty,
            total_points=test.total_points,
            time_limit=test.time_limit,
            questions=[QuestionResponse(**q) for q in test.questions],
            created_at=test.created_at
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{test_id}",
    response_model=TestResponse,
    summary="Get test by ID",
    description="Retrieve a specific test (owner or enrolled students)"
)
async def get_test(
    test_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get test by ID."""
    from sqlalchemy import select, and_
    from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
    
    test_repo = TestRepository(db)
    course_repo = CourseRepository(db)
    lecture_repo = LectureRepository(db)
    
    # Get test
    test = await test_repo.get_by_id(test_id)
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тест олдсонгүй"
        )
    
    # Check access: owner or enrolled student
    lecture = await lecture_repo.get_by_id(test.lecture_id)
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лекц олдсонгүй"
        )
    
    course = await course_repo.get_by_id(lecture.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Хичээл олдсонгүй"
        )
    
    has_access = course.owner_id == current_user.id
    
    if not has_access and current_user.role == "student":
        # Check enrollment
        enrollment_result = await db.execute(
            select(CourseEnrollmentModel).where(
                and_(
                    CourseEnrollmentModel.course_id == lecture.course_id,
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
            detail="Хандах эрхгүй байна"
        )
    
    return TestResponse(
        id=test.id,
        lecture_id=test.lecture_id,
        title=test.title,
        difficulty=test.difficulty,
        total_points=test.total_points,
        time_limit=test.time_limit,
        questions=[QuestionResponse(**q) for q in test.questions],
        created_at=test.created_at
    )


@router.get(
    "/lecture/{lecture_id}",
    response_model=TestListResponse,
    summary="Get tests for lecture",
    description="Get all tests for a specific lecture (owner or enrolled students)"
)
async def get_lecture_tests(
    lecture_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get all tests for a lecture."""
    from sqlalchemy import select, and_
    from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
    
    test_repo = TestRepository(db)
    lecture_repo = LectureRepository(db)
    course_repo = CourseRepository(db)
    
    # Get lecture
    lecture = await lecture_repo.get_by_id(lecture_id)
    
    if not lecture:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лекц олдсонгүй"
        )
    
    # Check access: owner or enrolled student
    course = await course_repo.get_by_id(lecture.course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Хичээл олдсонгүй"
        )
    
    has_access = course.owner_id == current_user.id
    
    if not has_access and current_user.role == "student":
        # Check enrollment
        enrollment_result = await db.execute(
            select(CourseEnrollmentModel).where(
                and_(
                    CourseEnrollmentModel.course_id == lecture.course_id,
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
            detail="Access denied"
        )
    
    # Get tests
    tests = await test_repo.get_by_lecture(lecture_id)
    
    # Filter tests: show only user's own tests if student
    if current_user.role == "student":
        tests = [t for t in tests if t.created_by == current_user.id]
    
    return TestListResponse(
        total=len(tests),
        tests=[
            TestResponse(
                id=t.id,
                lecture_id=t.lecture_id,
                title=t.title,
                difficulty=t.difficulty,
                total_points=t.total_points,
                time_limit=t.time_limit,
                questions=[QuestionResponse(**q) for q in t.questions],
                created_at=t.created_at
            )
            for t in tests
        ]
    )
