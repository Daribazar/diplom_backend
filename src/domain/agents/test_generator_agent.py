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

    def __init__(self, llm_adapter: ILLMAdapter, context_retriever: ContextRetriever):
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
        question_count: int = 10,
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
        context = await self.retriever.retrieve_for_test_generation(
            lecture_ids=lecture_ids,
            topic="lecture content, key concepts, examples, definitions",
            top_k=5,
        )
        if not context or not context.strip():
            logger.warning("No context for lectures=%s, using fallback", lecture_ids)
            context = "This is a lecture about neural networks, machine learning, and deep learning concepts."

        questions = await self._generate_questions(
            context=context,
            difficulty=difficulty,
            question_types=question_types,
            question_count=question_count,
        )

        allowed = set(question_types)
        validated = [
            q for q in self._validate_questions(questions) if q.type in allowed
        ]

        return TestGenerationResult(
            questions=validated,
            total_points=sum(q.points for q in validated),
            metadata={
                "difficulty": difficulty.value,
                "question_count": len(validated),
                "context_chunks": len(context),
            },
        )

    async def _generate_questions(
        self,
        context: str,
        difficulty: Difficulty,
        question_types: List[QuestionType],
        question_count: int,
    ) -> List[Question]:
        """Generate questions using LLM with RAG context."""
        response = await self.llm.complete(
            prompt=self._build_user_prompt(
                context, difficulty, question_types, question_count
            ),
            system_prompt=self._build_system_prompt(difficulty, question_types),
            temperature=0.7,
            max_tokens=4000,
        )
        return self._parse_questions(response.content)

    # JSON examples per question type, used to compose system prompt dynamically.
    _TYPE_EXAMPLES = {
        QuestionType.MCQ: """{
            "question_id": "q1",
            "type": "mcq",
            "question_text": "Асуултын текст монгол хэл дээр?",
            "options": ["Сонголт А", "Сонголт Б", "Сонголт В", "Сонголт Г"],
            "correct_answer": "Сонголт Б",
            "points": 2,
            "difficulty": "easy",
            "bloom_level": "remember",
            "explanation": "Тайлбар монгол хэл дээр..."
        }""",
        QuestionType.TRUE_FALSE: """{
            "question_id": "q1",
            "type": "true_false",
            "question_text": "Мэдэгдэл монгол хэл дээр.",
            "options": ["Үнэн", "Худал"],
            "correct_answer": "Үнэн",
            "points": 1,
            "difficulty": "easy",
            "bloom_level": "remember",
            "explanation": "Яагаад үнэн/худал болохыг тайлбарла..."
        }""",
        QuestionType.ESSAY: """{
            "question_id": "q1",
            "type": "essay",
            "question_text": "Эссэ асуултын текст?",
            "correct_answer": "Загвар хариулт: Энэ асуултад ... гэж бүрэн хариулна. Үндсэн санаануудыг дурдаж, жишээгээр баталгаажуулна.",
            "points": 5,
            "difficulty": "hard",
            "bloom_level": "evaluate",
            "explanation": "Нэмэлт тайлбар, гол санаанууд",
            "rubric": {
                "excellent": "Бүх үндсэн санааг жишээтэйгээр тайлбарласан (5 оноо)",
                "good": "Гол санааг тайлбарласан (4 оноо)",
                "satisfactory": "Үндсэн ойлголт нэрлэсэн (3 оноо)"
            }
        }""",
    }

    _TYPE_QUALITY_RULES = {
        QuestionType.MCQ: "- MCQ: Create 4 plausible options where distractors are reasonable but incorrect. Set `options` to 4 strings and `correct_answer` to one of them.",
        QuestionType.TRUE_FALSE: '- True/False: Make statements clear and unambiguous. `options` MUST be exactly ["Үнэн", "Худал"] and `correct_answer` MUST be one of those two strings.',
        QuestionType.ESSAY: "- Essay: Provide a concrete model answer in `correct_answer` (3-6 sentences in Mongolian). You may ALSO provide a `rubric` object, but `correct_answer` is REQUIRED.",
    }

    def _build_system_prompt(
        self, difficulty: Difficulty, question_types: List[QuestionType]
    ) -> str:
        """Build system prompt based on difficulty and requested question types."""
        bloom_mapping = {
            Difficulty.EASY: "Remember and Understand (recall facts, explain concepts)",
            Difficulty.MEDIUM: "Apply and Analyze (use knowledge, break down problems)",
            Difficulty.HARD: "Evaluate and Create (judge, design, synthesize)",
        }

        allowed_types_str = ", ".join(t.value for t in question_types)
        quality_rules = "\n".join(
            self._TYPE_QUALITY_RULES[t] for t in question_types
        )
        examples = ",\n        ".join(
            self._TYPE_EXAMPLES[t] for t in question_types
        )

        return f"""You are an expert educational assessment designer specializing in creating high-quality test questions.

CRITICAL REQUIREMENTS:
1. Generate questions in MONGOLIAN language (Монгол хэл)
2. Questions MUST be based ONLY on the provided lecture material
3. Answers MUST be factually correct according to the context
4. Create realistic and challenging questions that test true understanding
5. ALLOWED QUESTION TYPES: ONLY {allowed_types_str}. DO NOT generate any other type. Every question's `type` field MUST be one of: {allowed_types_str}.

Difficulty Level: {difficulty.value.upper()}
Bloom's Taxonomy Level: {bloom_mapping[difficulty]}

QUESTION QUALITY STANDARDS:
{quality_rules}
- All questions must be grammatically correct in Mongolian
- Use proper Mongolian terminology for technical concepts

OUTPUT FORMAT (JSON only, no additional text):
{{
    "questions": [
        {examples}
    ]
}}

IMPORTANT:
- Output ONLY valid JSON. No markdown, no explanations, just the JSON object.
- EVERY question's `type` field MUST be one of: {allowed_types_str}. No exceptions.
- For essay questions, `correct_answer` MUST contain a concrete sample answer text,
  never the rubric/criteria."""

    # ~4 chars/token; keep total prompt under provider TPM limits (Groq free 12K).
    MAX_CONTEXT_CHARS = 10000

    _TYPE_LABELS_MN = {
        QuestionType.MCQ: "Олон сонголттой (MCQ)",
        QuestionType.TRUE_FALSE: "Үнэн/Худал",
        QuestionType.ESSAY: "Эссэ",
    }

    def _build_user_prompt(
        self,
        context_text: str,
        difficulty: Difficulty,
        question_types: List[QuestionType],
        question_count: int,
    ) -> str:
        """Build user prompt with context."""
        types_str = ", ".join(t.value for t in question_types)
        types_mn = ", ".join(self._TYPE_LABELS_MN[t] for t in question_types)

        context = context_text[: self.MAX_CONTEXT_CHARS]
        if len(context_text) > self.MAX_CONTEXT_CHARS:
            context += "\n...[материал тасалсан]"

        return f"""Дараах хичээлийн материал дээр үндэслэн ЯГ {question_count} асуулт үүсгэнэ үү.

ХИЧЭЭЛИЙН МАТЕРИАЛ:
{context}

ШААРДЛАГА:
- Зөвшөөрөгдсөн асуултын төрөл: {types_mn} (`type` талбарт зөвхөн: {types_str})
- Бусад төрөл огт оруулж БОЛОХГҮЙ
- Бүх {question_count} асуулт {types_str} төрлийн байх ёстой
- Хүндрэл: {difficulty.value}
- Бүх асуулт МОНГОЛ хэл дээр байх ёстой
- Асуултууд хичээлийн материалд үндэслэсэн байх ёстой

Асуултуудыг JSON форматаар үүсгэнэ үү:"""

    @staticmethod
    def _extract_correct_answer(q_data: Dict) -> str:
        """Return correct_answer as a string, with rubric fallback for essays."""
        if "correct_answer" in q_data and q_data["correct_answer"] is not None:
            return str(q_data["correct_answer"])
        if q_data.get("type") == QuestionType.ESSAY.value:
            rubric = q_data.get("rubric")
            if rubric is not None:
                return json.dumps(rubric, ensure_ascii=False)
            return ""
        raise KeyError("correct_answer")

    def _build_question(self, q_data: Dict) -> Question:
        """Build a Question from raw LLM JSON data."""
        return Question(
            question_id=q_data["question_id"],
            type=QuestionType(q_data["type"]),
            question_text=q_data["question_text"],
            options=q_data.get("options"),
            correct_answer=self._extract_correct_answer(q_data),
            points=q_data["points"],
            difficulty=Difficulty(q_data["difficulty"]),
            bloom_level=q_data.get("bloom_level", "remember"),
            explanation=q_data.get("explanation", ""),
        )

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

            logger.info(
                "Parsed questions from LLM response count=%s", len(questions_data)
            )

            if not questions_data:
                logger.error("No questions in LLM response data=%s", data)
                raise ValueError("LLM response contains no questions")

            # Convert to Question objects
            questions = []
            for i, q_data in enumerate(questions_data):
                try:
                    question = self._build_question(q_data)
                    questions.append(question)
                except Exception as e:
                    logger.error(
                        "Error parsing question index=%s error=%s data=%s",
                        i,
                        str(e),
                        q_data,
                    )
                    continue

            logger.info(
                "Successfully created question objects count=%s", len(questions)
            )
            return questions

        except json.JSONDecodeError as e:
            logger.error(
                "JSON decode error=%s response_preview=%s", str(e), llm_response[:500]
            )
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
