"""Submit test use case."""
import uuid
from typing import List, Dict

from src.3_domain.entities.student_attempt import StudentAttempt
from src.3_domain.agents.evaluation_agent import EvaluationAgent
from src.4_infrastructure.database.repositories.student_attempt_repository import StudentAttemptRepository
from src.4_infrastructure.database.repositories.test_repository import TestRepository
from src.core.exceptions import NotFoundError


class SubmitTestUseCase:
    """Use case: Submit test and get evaluation."""
    
    def __init__(
        self,
        attempt_repository: StudentAttemptRepository,
        test_repository: TestRepository,
        evaluation_agent: EvaluationAgent
    ):
        """
        Initialize use case.
        
        Args:
            attempt_repository: Student attempt repository
            test_repository: Test repository
            evaluation_agent: Evaluation agent
        """
        self.attempt_repo = attempt_repository
        self.test_repo = test_repository
        self.evaluator = evaluation_agent
    
    async def execute(
        self,
        test_id: str,
        student_id: str,
        answers: List[Dict]
    ) -> StudentAttempt:
        """
        Submit test and get evaluation.
        
        Args:
            test_id: Test ID
            student_id: Student ID
            answers: List of {question_id, answer}
            
        Returns:
            Graded StudentAttempt
            
        Raises:
            NotFoundError: If test not found
        """
        # Get test
        test = await self.test_repo.get_by_id(test_id)
        
        if not test:
            raise NotFoundError(f"Test {test_id} not found")
        
        # Evaluate answers
        evaluation = await self.evaluator.evaluate(
            test_questions=test.questions,
            student_answers=answers
        )
        
        # Create attempt
        attempt = StudentAttempt(
            id=f"attempt_{uuid.uuid4().hex[:12]}",
            student_id=student_id,
            test_id=test_id,
            total_score=evaluation.total_score,
            percentage=evaluation.percentage,
            status="graded",
            answers=[
                {
                    "question_id": r.question_id,
                    "student_answer": r.student_answer,
                    "correct_answer": r.correct_answer,
                    "is_correct": r.is_correct,
                    "points_earned": r.points_earned,
                    "max_points": r.max_points,
                    "feedback": r.feedback
                }
                for r in evaluation.question_results
            ],
            weak_topics=evaluation.weak_topics,
            analytics=evaluation.analytics
        )
        
        attempt.mark_as_submitted()
        
        # Save to database
        saved_attempt = await self.attempt_repo.create(attempt)
        
        return saved_attempt
