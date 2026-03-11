"""Submit test use case."""
import uuid
from datetime import datetime
from typing import Dict, List, Any

from src.domain.entities.student_attempt import StudentAttempt
from src.infrastructure.database.repositories.test_repository import TestRepository
from src.infrastructure.database.repositories.student_attempt_repository import StudentAttemptRepository
from src.domain.agents.evaluation_agent import EvaluationAgent
from src.core.exceptions import NotFoundError


class SubmitTestUseCase:
    """Use case for submitting and evaluating test."""
    
    def __init__(
        self,
        attempt_repo: StudentAttemptRepository,
        test_repo: TestRepository,
        evaluation_agent: EvaluationAgent
    ):
        """Initialize use case."""
        self.attempt_repo = attempt_repo
        self.test_repo = test_repo
        self.evaluation_agent = evaluation_agent
    
    async def execute(
        self,
        test_id: str,
        user_id: str,
        answers: List[Dict[str, Any]]
    ) -> StudentAttempt:
        """
        Submit test and get evaluation.
        
        Args:
            test_id: Test identifier
            user_id: Student user ID
            answers: List of answers [{question_id, answer}, ...]
            
        Returns:
            StudentAttempt entity with evaluation results
        """
        # Get test
        test = await self.test_repo.get_by_id(test_id)
        if not test:
            raise NotFoundError(f"Тест олдсонгүй: {test_id}")
        
        # Evaluate answers using AI agent
        evaluation_result = await self.evaluation_agent.evaluate(
            test_questions=test.questions,
            student_answers=answers
        )
        
        # Convert QuestionResult objects to dictionaries
        question_results_dict = [
            {
                "question_id": qr.question_id,
                "student_answer": qr.student_answer,
                "correct_answer": qr.correct_answer,
                "is_correct": qr.is_correct,
                "points_earned": qr.points_earned,
                "max_points": qr.max_points,
                "feedback": qr.feedback
            }
            for qr in evaluation_result.question_results
        ]
        
        # Create attempt entity
        attempt = StudentAttempt(
            id=f"attempt_{uuid.uuid4().hex[:12]}",
            student_id=user_id,
            test_id=test_id,
            total_score=evaluation_result.total_score,
            percentage=evaluation_result.percentage,
            status="graded",
            answers=question_results_dict,
            weak_topics=evaluation_result.weak_topics,
            analytics=evaluation_result.analytics
            # submitted_at will be set to created_at by repository
        )
        
        # Save to database
        created_attempt = await self.attempt_repo.create(attempt)
        
        return created_attempt
