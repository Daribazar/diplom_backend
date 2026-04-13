"""Test evaluation endpoints."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, CurrentUser
from src.infrastructure.database.repositories.student_attempt_repository import StudentAttemptRepository
from src.infrastructure.database.repositories.test_repository import TestRepository
from src.infrastructure.external.llm.llm_factory import LLMFactory
from src.domain.agents.evaluation_agent import EvaluationAgent
from src.application.usecases.evaluation.submit_test import SubmitTestUseCase
from src.presentation.schemas.evaluation import (
    SubmitTestRequest,
    EvaluationResponse,
    QuestionResultResponse,
    TestAttemptsResponse,
    AttemptSummaryResponse,
)
from src.core.exceptions import NotFoundError
from src.presentation.api.http_errors import map_common_domain_error

router = APIRouter()
OVERALL_FEEDBACK_CACHED = "(Cached feedback)"
PERFECT_SCORE_THRESHOLD = 99.5
PERFECT_SCORE_FEEDBACK = (
    "Маш сайн! Та энэ тестийг 100% зөв хийлээ. "
    "Энэ эрчээрээ үргэлжлүүлээрэй."
)


def _to_evaluation_response(attempt, overall_feedback: str) -> EvaluationResponse:
    return EvaluationResponse(
        attempt_id=attempt.id,
        test_id=attempt.test_id,
        total_score=attempt.total_score,
        percentage=attempt.percentage,
        status=attempt.status,
        answers=[QuestionResultResponse(**ans) for ans in attempt.answers],
        weak_topics=attempt.weak_topics,
        analytics=attempt.analytics,
        overall_feedback=overall_feedback,
        created_at=attempt.created_at,
    )


def _evaluation_repositories(db: AsyncSession) -> tuple[StudentAttemptRepository, TestRepository]:
    return StudentAttemptRepository(db), TestRepository(db)


def _build_submit_use_case(db: AsyncSession) -> tuple[SubmitTestUseCase, EvaluationAgent]:
    attempt_repo, test_repo = _evaluation_repositories(db)
    llm = LLMFactory.create_default_adapter()
    evaluation_agent = EvaluationAgent(llm)
    use_case = SubmitTestUseCase(attempt_repo, test_repo, evaluation_agent)
    return use_case, evaluation_agent


def _to_attempt_summary(attempt) -> AttemptSummaryResponse:
    return AttemptSummaryResponse(
        attempt_id=attempt.id,
        total_score=attempt.total_score,
        percentage=attempt.percentage,
        status=attempt.status,
        created_at=attempt.created_at.isoformat() if attempt.created_at else None,
    )


async def _require_owned_attempt(
    attempt_repo: StudentAttemptRepository, attempt_id: str, user_id: str
):
    attempt = await attempt_repo.get_by_id(attempt_id)
    if not attempt:
        raise NotFoundError("Оролдлого олдсонгүй")
    if attempt.student_id != user_id:
        raise PermissionError("Хандах эрхгүй байна")
    return attempt


def _enrich_attempt_answers(attempt_answers: list, test) -> list[QuestionResultResponse]:
    """Fill missing question_text in attempt answers from test payload."""
    enriched_answers: list[QuestionResultResponse] = []
    for answer_item in attempt_answers:
        answer = dict(answer_item)
        if not answer.get("question_text") and test:
            question = next(
                (q for q in test.questions if q["question_id"] == answer["question_id"]),
                None,
            )
            answer["question_text"] = question.get("question_text", "") if question else ""
        enriched_answers.append(QuestionResultResponse(**answer))
    return enriched_answers


@router.post(
    "/submit/{test_id}",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit test and get evaluation",
    description="Submit test answers and receive immediate AI-powered evaluation"
)
async def submit_test(
    test_id: str,
    request: SubmitTestRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit test and get immediate evaluation.
    
    Request body:
    ```json
    {
        "answers": [
            {"question_id": "q1", "answer": "Option A"},
            {"question_id": "q2", "answer": "True"},
            {"question_id": "q3", "answer": "Essay answer here..."}
        ]
    }
    ```
    
    Response includes:
    - Auto-graded MCQ and True/False questions
    - AI-graded essay questions
    - Detailed feedback for each question
    - Overall performance analytics
    - Weak topic identification
    - Personalized feedback in Mongolian
    """
    use_case, evaluation_agent = _build_submit_use_case(db)
    
    try:
        answers_data = [answer.model_dump() for answer in request.answers]
        # Execute evaluation
        attempt = await use_case.execute(
            test_id=test_id,
            user_id=current_user.id,  # Changed from student_id to user_id
            answers=answers_data
        )
        
        # Get overall feedback from evaluation agent
        overall_feedback = await evaluation_agent._generate_overall_feedback(
            percentage=attempt.percentage,
            weak_topics=attempt.weak_topics,
            analytics=attempt.analytics
        )
        
        return _to_evaluation_response(attempt, overall_feedback)
        
    except (NotFoundError, ValueError, PermissionError) as e:
        raise map_common_domain_error(e)


@router.get(
    "/attempt/{attempt_id}",
    response_model=EvaluationResponse,
    summary="Get attempt result",
    description="Retrieve a previous test attempt result"
)
async def get_attempt_result(
    attempt_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get test attempt result by ID."""
    attempt_repo, test_repo = _evaluation_repositories(db)
    llm = LLMFactory.create_default_adapter()
    evaluation_agent = EvaluationAgent(llm)

    try:
        attempt = await _require_owned_attempt(attempt_repo, attempt_id, current_user.id)
        test = await test_repo.get_by_id(attempt.test_id)
        enriched_answers = _enrich_attempt_answers(attempt.answers, test)
        if (attempt.percentage or 0) >= PERFECT_SCORE_THRESHOLD:
            overall_feedback = PERFECT_SCORE_FEEDBACK
        else:
            try:
                overall_feedback = await evaluation_agent._generate_overall_feedback(
                    percentage=attempt.percentage,
                    weak_topics=attempt.weak_topics or [],
                    analytics=attempt.analytics or {},
                )
            except Exception:
                overall_feedback = OVERALL_FEEDBACK_CACHED
        return EvaluationResponse(
            attempt_id=attempt.id,
            test_id=attempt.test_id,
            total_score=attempt.total_score,
            percentage=attempt.percentage,
            status=attempt.status,
            answers=enriched_answers,
            weak_topics=attempt.weak_topics,
            analytics=attempt.analytics,
            overall_feedback=overall_feedback,
            created_at=attempt.created_at,
        )
    except (NotFoundError, ValueError, PermissionError) as e:
        raise map_common_domain_error(e)


@router.get(
    "/test/{test_id}/attempts",
    response_model=TestAttemptsResponse,
    summary="Get all attempts for a test",
    description="Get all attempts by current user for a specific test"
)
async def get_test_attempts(
    test_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get all attempts for a test by current user."""
    attempt_repo, _ = _evaluation_repositories(db)
    
    # Get attempts
    attempts = await attempt_repo.get_by_student_and_test(
        student_id=current_user.id,
        test_id=test_id
    )
    
    return TestAttemptsResponse(
        test_id=test_id,
        total_attempts=len(attempts),
        attempts=[_to_attempt_summary(attempt) for attempt in attempts],
    )
