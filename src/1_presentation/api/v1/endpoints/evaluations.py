"""Test evaluation endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, CurrentUser
from src.4_infrastructure.database.repositories.student_attempt_repository import StudentAttemptRepository
from src.4_infrastructure.database.repositories.test_repository import TestRepository
from src.4_infrastructure.external.llm.llm_factory import LLMFactory
from src.3_domain.agents.evaluation_agent import EvaluationAgent
from src.2_application.usecases.evaluation.submit_test import SubmitTestUseCase
from src.1_presentation.schemas.evaluation import (
    SubmitTestRequest,
    EvaluationResponse,
    QuestionResultResponse
)
from src.core.exceptions import NotFoundError

router = APIRouter()


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
    # Initialize repositories
    attempt_repo = StudentAttemptRepository(db)
    test_repo = TestRepository(db)
    
    # Initialize LLM for evaluation
    llm = LLMFactory.create_default_adapter()
    evaluation_agent = EvaluationAgent(llm)
    
    # Initialize use case
    use_case = SubmitTestUseCase(
        attempt_repo,
        test_repo,
        evaluation_agent
    )
    
    try:
        # Execute evaluation
        attempt = await use_case.execute(
            test_id=test_id,
            student_id=current_user.id,
            answers=request.answers
        )
        
        # Get overall feedback from evaluation agent
        overall_feedback = await evaluation_agent._generate_overall_feedback(
            percentage=attempt.percentage,
            weak_topics=attempt.weak_topics,
            analytics=attempt.analytics
        )
        
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
            created_at=attempt.created_at
        )
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


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
    attempt_repo = StudentAttemptRepository(db)
    
    # Get attempt
    attempt = await attempt_repo.get_by_id(attempt_id)
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attempt not found"
        )
    
    # Check ownership
    if attempt.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return EvaluationResponse(
        attempt_id=attempt.id,
        test_id=attempt.test_id,
        total_score=attempt.total_score,
        percentage=attempt.percentage,
        status=attempt.status,
        answers=[QuestionResultResponse(**ans) for ans in attempt.answers],
        weak_topics=attempt.weak_topics,
        analytics=attempt.analytics,
        overall_feedback="(Cached feedback)",
        created_at=attempt.created_at
    )


@router.get(
    "/test/{test_id}/attempts",
    response_model=dict,
    summary="Get all attempts for a test",
    description="Get all attempts by current user for a specific test"
)
async def get_test_attempts(
    test_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get all attempts for a test by current user."""
    attempt_repo = StudentAttemptRepository(db)
    
    # Get attempts
    attempts = await attempt_repo.get_by_student_and_test(
        student_id=current_user.id,
        test_id=test_id
    )
    
    return {
        "test_id": test_id,
        "total_attempts": len(attempts),
        "attempts": [
            {
                "attempt_id": a.id,
                "total_score": a.total_score,
                "percentage": a.percentage,
                "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in attempts
        ]
    }
