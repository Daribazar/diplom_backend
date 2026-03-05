"""Generate test use case."""
import uuid
from typing import List

from src.3_domain.entities.test import Test
from src.3_domain.agents.test_generator_agent import (
    TestGeneratorAgent,
    QuestionType,
    Difficulty
)
from src.4_infrastructure.database.repositories.test_repository import TestRepository
from src.4_infrastructure.database.repositories.lecture_repository import LectureRepository
from src.4_infrastructure.database.repositories.course_repository import CourseRepository
from src.core.exceptions import NotFoundError, UnauthorizedError


class GenerateTestUseCase:
    """Use case: Generate test using AI."""
    
    def __init__(
        self,
        test_repository: TestRepository,
        lecture_repository: LectureRepository,
        course_repository: CourseRepository,
        test_generator: TestGeneratorAgent
    ):
        """
        Initialize use case.
        
        Args:
            test_repository: Test repository
            lecture_repository: Lecture repository
            course_repository: Course repository
            test_generator: Test generator agent
        """
        self.test_repo = test_repository
        self.lecture_repo = lecture_repository
        self.course_repo = course_repository
        self.generator = test_generator
    
    async def execute(
        self,
        course_id: str,
        week_number: int,
        user_id: str,
        difficulty: str = "medium",
        question_types: List[str] = None,
        question_count: int = 10
    ) -> Test:
        """
        Generate test for a week.
        
        Business rules:
        - User must own the course
        - Lecture must be processed
        
        Args:
            course_id: Course ID
            week_number: Week number
            user_id: User ID
            difficulty: Difficulty level
            question_types: Question types
            question_count: Number of questions
            
        Returns:
            Created test
            
        Raises:
            NotFoundError: If course/lecture not found
            UnauthorizedError: If user doesn't own course
            ValueError: If lecture not ready
        """
        # Validate course ownership
        course = await self.course_repo.get_by_id(course_id)
        
        if not course:
            raise NotFoundError(f"Course {course_id} not found")
        
        if course.owner_id != user_id:
            raise UnauthorizedError("You don't own this course")
        
        # Check lecture exists and is processed
        lecture = await self.lecture_repo.get_by_course_and_week(
            course_id, week_number
        )
        
        if not lecture:
            raise NotFoundError(f"No lecture found for week {week_number}")
        
        if lecture.status != "completed":
            raise ValueError(
                f"Lecture not ready for test generation. Status: {lecture.status}"
            )
        
        # Parse parameters
        difficulty_enum = Difficulty(difficulty)
        
        if question_types is None:
            question_types = ["mcq", "true_false"]
        
        question_type_enums = [QuestionType(qt) for qt in question_types]
        
        # Generate test (AI Agent with RAG)
        result = await self.generator.generate_test(
            lecture_ids=[lecture.id],
            difficulty=difficulty_enum,
            question_types=question_type_enums,
            question_count=question_count
        )
        
        # Create Test entity
        test = Test(
            id=f"test_{uuid.uuid4().hex[:12]}",
            lecture_id=lecture.id,
            title=f"Week {week_number} Test - {difficulty.capitalize()}",
            difficulty=difficulty,
            total_points=result.total_points,
            time_limit=30,  # 30 minutes default
            questions=[
                {
                    "question_id": q.question_id,
                    "type": q.type.value,
                    "question_text": q.question_text,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "points": q.points,
                    "difficulty": q.difficulty.value,
                    "bloom_level": q.bloom_level,
                    "explanation": q.explanation
                }
                for q in result.questions
            ]
        )
        
        # Save to database
        created_test = await self.test_repo.create(test)
        
        return created_test
