"""Test generator agent with RAG."""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from src.domain.interfaces.llm_adapter import ILLMAdapter
from src.domain.memory.context_retriever import ContextRetriever


class QuestionType(str, Enum):
    """Question types."""
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    ESSAY = "essay"


class Difficulty(str, Enum):
    """Difficulty levels (Bloom's Taxonomy)."""
    EASY = "easy"  # Remember, Understand
    MEDIUM = "medium"  # Apply, Analyze
    HARD = "hard"  # Evaluate, Create


@dataclass
class Question:
    """Test question."""
    question_id: str
    type: QuestionType
    question_text: str
    options: Optional[List[str]]  # For MCQ, True/False
    correct_answer: str
    points: int
    difficulty: Difficulty
    bloom_level: str
    explanation: str


@dataclass
class TestGenerationResult:
    """Test generation result."""
    questions: List[Question]
    total_points: int
    metadata: Dict


class TestGeneratorAgent:
    """
    Test Generator Agent - generates tests using RAG.
    
    Workflow:
    1. Retrieve context from lecture (RAG)
    2. Generate questions using LLM
    3. Validate quality
    4. Format output
    """
    
    def __init__(
        self,
        llm_adapter: ILLMAdapter,
        context_retriever: ContextRetriever
    ):
        """
        Initialize test generator agent.
        
        Args:
            llm_adapter: LLM adapter for generation
            context_retriever: RAG context retriever
        """
        self.llm = llm_adapter
        self.retriever = context_retriever
    
    async def generate_test(
        self,
        lecture_ids: List[str],
        difficulty: Difficulty,
        question_types: List[QuestionType],
        question_count: int = 10
    ) -> TestGenerationResult:
        """
        Generate test for lectures.
        
        Args:
            lecture_ids: Lecture IDs to generate from
            difficulty: Difficulty level
            question_types: Types of questions to generate
            question_count: Total questions
            
        Returns:
            TestGenerationResult
        """
        # Step 1: RAG - Retrieve context
        query = "lecture content, key concepts, examples, definitions"
        context_chunks = await self.retriever.retrieve_for_test_generation(
            lecture_ids=lecture_ids,
            topic=query,
            top_k=5
        )
        
        if not context_chunks:
            raise ValueError("No lecture content found for test generation")
        
        # Step 2: Generate questions
        questions = await self._generate_questions(
            context=context_chunks,
            difficulty=difficulty,
            question_types=question_types,
            question_count=question_count
        )
        
        # Step 3: Validate quality
        validated_questions = self._validate_questions(questions)
        
        # Step 4: Calculate points
        total_points = sum(q.points for q in validated_questions)
        
        return TestGenerationResult(
            questions=validated_questions,
            total_points=total_points,
            metadata={
                "difficulty": difficulty.value,
                "question_count": len(validated_questions),
                "context_chunks": len(context_chunks)
            }
        )
    
    async def _generate_questions(
        self,
        context: str,
        difficulty: Difficulty,
        question_types: List[QuestionType],
        question_count: int
    ) -> List[Question]:
        """Generate questions using LLM with RAG context."""
        # Build system prompt
        system_prompt = self._build_system_prompt(difficulty)
        
        # Build user prompt with context
        user_prompt = self._build_user_prompt(
            context_text=context,
            difficulty=difficulty,
            question_types=question_types,
            question_count=question_count
        )
        
        # LLM generation
        response = await self.llm.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=3000
        )
        
        # Parse JSON response
        questions = self._parse_questions(response.content)
        
        return questions
    
    def _build_system_prompt(self, difficulty: Difficulty) -> str:
        """Build system prompt based on difficulty."""
        bloom_mapping = {
            Difficulty.EASY: "Remember and Understand (recall facts, explain concepts)",
            Difficulty.MEDIUM: "Apply and Analyze (use knowledge, break down problems)",
            Difficulty.HARD: "Evaluate and Create (judge, design, synthesize)"
        }
        
        return f"""You are an expert educational assessment designer.
Generate high-quality test questions based on provided lecture material.

Difficulty Level: {difficulty.value.upper()}
Bloom's Taxonomy Level: {bloom_mapping[difficulty]}

CRITICAL REQUIREMENTS:
1. Questions MUST be based ONLY on the provided context
2. Answers MUST be factually correct according to the context
3. For MCQ: Create plausible distractors (wrong options that seem reasonable)
4. For True/False: Make statements clear and unambiguous
5. For Essay: Provide clear rubric and expected answer
6. Output ONLY valid JSON, no additional text

OUTPUT FORMAT (JSON):
{{
    "questions": [
        {{
            "question_id": "q1",
            "type": "mcq",
            "question_text": "What is the definition of integral?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "points": 2,
            "difficulty": "easy",
            "bloom_level": "remember",
            "explanation": "According to the lecture..."
        }}
    ]
}}"""
    
    def _build_user_prompt(
        self,
        context_text: str,
        difficulty: Difficulty,
        question_types: List[QuestionType],
        question_count: int
    ) -> str:
        """Build user prompt with context."""
        types_str = ", ".join([t.value for t in question_types])
        
        return f"""Based on the following lecture material, generate {question_count} test questions.

LECTURE MATERIAL:
{context_text}

REQUIREMENTS:
- Question types: {types_str}
- Difficulty: {difficulty.value}
- Total questions: {question_count}
- Distribute points appropriately (MCQ: 1-2pts, True/False: 1pt, Essay: 3-5pts)

Generate questions now in JSON format:"""
    
    def _parse_questions(self, llm_response: str) -> List[Question]:
        """Parse LLM response to Question objects."""
        try:
            # Remove markdown code blocks if present
            response_text = llm_response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            data = json.loads(response_text)
            questions_data = data.get("questions", [])
            
            # Convert to Question objects
            questions = []
            for q_data in questions_data:
                question = Question(
                    question_id=q_data["question_id"],
                    type=QuestionType(q_data["type"]),
                    question_text=q_data["question_text"],
                    options=q_data.get("options"),
                    correct_answer=q_data["correct_answer"],
                    points=q_data["points"],
                    difficulty=Difficulty(q_data["difficulty"]),
                    bloom_level=q_data.get("bloom_level", "remember"),
                    explanation=q_data.get("explanation", "")
                )
                questions.append(question)
            
            return questions
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
    
    def _validate_questions(self, questions: List[Question]) -> List[Question]:
        """Validate and filter questions."""
        validated = []
        
        for q in questions:
            # Basic validation
            if not q.question_text or len(q.question_text) < 10:
                continue  # Too short
            
            if q.type == QuestionType.MCQ:
                if not q.options or len(q.options) < 2:
                    continue  # Not enough options
                if q.correct_answer not in q.options:
                    continue  # Invalid answer
            
            if q.points < 1:
                q.points = 1  # Minimum points
            
            validated.append(q)
        
        return validated
