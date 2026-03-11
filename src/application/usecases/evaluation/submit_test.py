"""Submit test use case."""
from typing import Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.repositories.test_repository import TestRepository
from src.infrastructure.database.repositories.student_attempt_repository import StudentAttemptRepository
from src.domain.agents.evaluation_agent import EvaluationAgent
from src.core.exceptions import NotFoundError


class SubmitTestUseCase:
    """Use case for submitting and evaluating test."""
    
    def __init__(
        self,
        test_repo: TestRepository,
        attempt_repo: StudentAttemptRepository,
        evaluation_agent: EvaluationAgent
    ):
        """Initialize use case."""
        self.test_repo = test_repo
        self.attempt_repo = attempt_repo
        self.evaluation_agent = evaluation_agent
    
    async def execute(
        self,
        test_id: str,
        user_id: str,
        answers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Submit test and get evaluation.
        
        Args:
            test_id: Test identifier
            user_id: Student user ID
            answers: List of answers [{question_id, answer}, ...]
            
        Returns:
            Evaluation results with scores and feedback
        """
        # Get test
        test = await self.test_repo.get_by_id(test_id)
        if not test:
            raise NotFoundError(f"Test {test_id} not found")
        
        # Evaluate answers
        evaluation_result = await self.evaluation_agent.evaluate(
            test=test,
            answers=answers
        )
        
        # Save attempt
        attempt = await self.attempt_repo.create(
            test_id=test_id,
            user_id=user_id,
            answers=answers,
            score=evaluation_result["score"],
            feedback=evaluation_result["feedback"]
        )
        
        return {
            "attempt_id": attempt.id,
            "score": evaluation_result["score"],
            "max_score": evaluation_result["max_score"],
            "percentage": evaluation_result["percentage"],
            "feedback": evaluation_result["feedback"],
            "question_results": evaluation_result["question_results"]
        }
