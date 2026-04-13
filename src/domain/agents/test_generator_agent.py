"""Test generator agent with RAG."""
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from src.domain.interfaces.llm_adapter import ILLMAdapter
from src.domain.memory.context_retriever import ContextRetriever

logger = logging.getLogger(__name__)


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
        
        # Log context retrieval
        logger.info("Retrieved context chunks length=%s", len(context_chunks) if context_chunks else 0)
        
        if not context_chunks or len(context_chunks.strip()) == 0:
            logger.warning("No context found for lectures=%s", lecture_ids)
            # Use fallback context for mock generation
            context_chunks = "This is a lecture about neural networks, machine learning, and deep learning concepts."
        
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
            max_tokens=4000  # Increased for longer questions
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
        
        return f"""You are an expert educational assessment designer specializing in creating high-quality test questions.

CRITICAL REQUIREMENTS:
1. Generate questions in MONGOLIAN language (Монгол хэл)
2. Questions MUST be based ONLY on the provided lecture material
3. Answers MUST be factually correct according to the context
4. Create realistic and challenging questions that test true understanding

Difficulty Level: {difficulty.value.upper()}
Bloom's Taxonomy Level: {bloom_mapping[difficulty]}

QUESTION QUALITY STANDARDS:
- MCQ: Create 4 plausible options where distractors are reasonable but incorrect
- True/False: Make statements clear, unambiguous, and test key concepts
- Essay: Provide clear rubric with specific evaluation criteria
- All questions must be grammatically correct in Mongolian
- Use proper Mongolian terminology for technical concepts

OUTPUT FORMAT (JSON only, no additional text):
{{
    "questions": [
        {{
            "question_id": "q1",
            "type": "mcq",
            "question_text": "Асуултын текст монгол хэл дээр?",
            "options": ["Сонголт А", "Сонголт Б", "Сонголт В", "Сонголт Г"],
            "correct_answer": "Сонголт Б",
            "points": 2,
            "difficulty": "easy",
            "bloom_level": "remember",
            "explanation": "Тайлбар монгол хэл дээр..."
        }}
    ]
}}

IMPORTANT: Output ONLY valid JSON. No markdown, no explanations, just the JSON object."""
    
    def _build_user_prompt(
        self,
        context_text: str,
        difficulty: Difficulty,
        question_types: List[QuestionType],
        question_count: int
    ) -> str:
        """Build user prompt with context."""
        types_str = ", ".join([t.value for t in question_types])
        
        # Map question types to Mongolian
        type_mapping = {
            "mcq": "Олон сонголттой (MCQ)",
            "true_false": "Үнэн/Худал",
            "essay": "Эссэ"
        }
        types_mongolian = ", ".join([type_mapping.get(t.value, t.value) for t in question_types])
        
        return f"""Дараах хичээлийн материал дээр үндэслэн {question_count} асуулт үүсгэнэ үү.

ХИЧЭЭЛИЙН МАТЕРИАЛ:
{context_text}

ШААРДЛАГА:
- Асуултын төрөл: {types_mongolian} ({types_str})
- Хүндрэл: {difficulty.value}
- Нийт асуулт: {question_count}
- Оноо: MCQ (2 оноо), Үнэн/Худал (1 оноо), Эссэ (3-5 оноо)
- Бүх асуулт МОНГОЛ хэл дээр байх ёстой
- Асуултууд хичээлийн материалд үндэслэсэн байх ёстой

Асуултуудыг JSON форматаар үүсгэнэ үү:"""
    
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
            
            logger.debug("Parsing LLM response preview=%s", response_text[:200])
            
            # Parse JSON
            data = json.loads(response_text)
            questions_data = data.get("questions", [])
            
            logger.info("Parsed questions from LLM response count=%s", len(questions_data))
            
            if not questions_data:
                logger.error("No questions in LLM response data=%s", data)
                raise ValueError("LLM response contains no questions")
            
            # Convert to Question objects
            questions = []
            for i, q_data in enumerate(questions_data):
                try:
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
                except Exception as e:
                    logger.error("Error parsing question index=%s error=%s data=%s", i, str(e), q_data)
                    continue
            
            logger.info("Successfully created question objects count=%s", len(questions))
            return questions
            
        except json.JSONDecodeError as e:
            logger.error("JSON decode error=%s response_preview=%s", str(e), llm_response[:500])
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
