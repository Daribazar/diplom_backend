"""Evaluation agent for grading test submissions."""

from typing import List, Dict, Optional
from dataclasses import dataclass
import json

from src.domain.interfaces.llm_adapter import ILLMAdapter


@dataclass
class QuestionResult:
    """Individual question grading result."""

    question_id: str
    student_answer: str
    correct_answer: str
    is_correct: bool
    points_earned: float
    max_points: int
    feedback: Optional[str] = None


@dataclass
class EvaluationResult:
    """Complete evaluation result."""

    question_results: List[QuestionResult]
    total_score: float
    percentage: float
    weak_topics: List[str]
    analytics: Dict
    overall_feedback: str


class EvaluationAgent:
    """
    Evaluation Agent - grades student submissions.

    Capabilities:
    - Auto-grade MCQ and True/False
    - AI-grade Essay questions
    - Generate feedback
    - Identify weak topics
    """

    def __init__(self, llm_adapter: ILLMAdapter):
        """
        Initialize evaluation agent.

        Args:
            llm_adapter: LLM adapter for AI grading
        """
        self.llm = llm_adapter

    async def evaluate(
        self, test_questions: List[Dict], student_answers: List[Dict]
    ) -> EvaluationResult:
        """
        Evaluate student test submission.

        Args:
            test_questions: Questions from test
            student_answers: Student's answers

        Returns:
            EvaluationResult
        """
        # Create answer map
        answer_map = {ans["question_id"]: ans["answer"] for ans in student_answers}

        # Grade each question
        question_results = []
        total_score = 0.0
        max_score = 0

        for question in test_questions:
            q_id = question["question_id"]
            student_ans = answer_map.get(q_id, "")

            # Grade based on type
            if question["type"] in ["mcq", "true_false"]:
                result = self._grade_objective(question, student_ans)
            else:  # essay
                result = await self._grade_essay(question, student_ans)

            question_results.append(result)
            total_score += result.points_earned
            max_score += result.max_points

        # Calculate percentage
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        # Analyze weak topics
        weak_topics = self._identify_weak_topics(question_results, test_questions)

        # Generate analytics
        analytics = self._generate_analytics(question_results, test_questions)

        # Overall feedback
        overall_feedback = await self._generate_overall_feedback(
            percentage, weak_topics, analytics
        )

        return EvaluationResult(
            question_results=question_results,
            total_score=total_score,
            percentage=percentage,
            weak_topics=weak_topics,
            analytics=analytics,
            overall_feedback=overall_feedback,
        )

    def _grade_objective(self, question: Dict, student_answer: str) -> QuestionResult:
        """Auto-grade MCQ/True-False."""
        # Ensure student_answer is string
        if not isinstance(student_answer, str):
            student_answer = str(student_answer)

        correct_answer = question["correct_answer"]

        # Ensure correct_answer is string
        if not isinstance(correct_answer, str):
            correct_answer = str(correct_answer)

        # Normalize true/false answers for comparison
        def normalize_answer(ans: str) -> str:
            """Normalize answer to lowercase English for comparison."""
            ans_lower = ans.strip().lower()
            # Convert Mongolian to English
            if ans_lower in ["үнэн", "true"]:
                return "true"
            elif ans_lower in ["худал", "false"]:
                return "false"
            return ans_lower

        # Normalize both answers
        normalized_student = normalize_answer(student_answer)
        normalized_correct = normalize_answer(correct_answer)

        # Compare normalized answers
        is_correct = normalized_student == normalized_correct
        points_earned = question["points"] if is_correct else 0.0

        # Format correct answer for display (convert to Mongolian if needed)
        display_correct = correct_answer
        if normalized_correct == "true":
            display_correct = "Үнэн"
        elif normalized_correct == "false":
            display_correct = "Худал"

        return QuestionResult(
            question_id=question["question_id"],
            student_answer=student_answer,
            correct_answer=display_correct,
            is_correct=is_correct,
            points_earned=points_earned,
            max_points=question["points"],
            feedback="Зөв!" if is_correct else f"Буруу. Зөв хариулт: {display_correct}",
        )

    @staticmethod
    def _essay_reference_answer(question: Dict) -> str:
        """Build a human-readable reference answer for an essay question.

        Resolution order:
        1. ``correct_answer`` field if it is a concrete model answer (plain text).
        2. ``explanation`` field (key points / notes).
        3. ``rubric`` field formatted as labelled criteria.
        4. ``correct_answer`` field if it actually stores a rubric (legacy data),
           formatted for display.
        """

        def _format_rubric(rubric: Dict) -> str:
            order = ["excellent", "good", "satisfactory", "poor"]
            keys = [k for k in order if k in rubric] + [
                k for k in rubric if k not in order
            ]
            label_map = {
                "excellent": "Маш сайн",
                "good": "Сайн",
                "satisfactory": "Дундаж",
                "poor": "Сул",
            }
            lines = []
            for k in keys:
                value = rubric[k]
                if isinstance(value, (list, tuple)):
                    value = "; ".join(str(v) for v in value)
                label = label_map.get(k, str(k).capitalize())
                lines.append(f"{label}: {value}")
            return "\n".join(lines)

        raw = question.get("correct_answer")
        correct_is_rubric = False
        correct_text = ""

        if raw:
            candidate = raw
            if isinstance(raw, str):
                try:
                    candidate = json.loads(raw)
                except (ValueError, TypeError):
                    candidate = raw.strip()
            if isinstance(candidate, dict):
                correct_is_rubric = True
                correct_rubric = candidate
            elif isinstance(candidate, str):
                correct_text = candidate.strip()
            else:
                correct_text = str(candidate).strip()

        # 1. Concrete model answer from correct_answer
        if correct_text:
            return correct_text

        # 2. Explanation as fallback
        explanation = (question.get("explanation") or "").strip()
        if explanation:
            return explanation

        # 3. Dedicated rubric field
        rubric_field = question.get("rubric")
        if isinstance(rubric_field, dict) and rubric_field:
            return "Үнэлгээний шалгуур:\n" + _format_rubric(rubric_field)

        # 4. Legacy: rubric stored in correct_answer
        if correct_is_rubric:
            return "Үнэлгээний шалгуур:\n" + _format_rubric(correct_rubric)

        return ""

    async def _grade_essay(self, question: Dict, student_answer: str) -> QuestionResult:
        """AI-grade essay question."""
        # Ensure student_answer is string
        if not isinstance(student_answer, str):
            student_answer = str(student_answer)

        reference_answer = self._essay_reference_answer(question)

        system_prompt = """You are an expert educational evaluator.
Grade the student's essay answer based on the rubric provided.

Rubric:
- Accuracy (40%): Factually correct
- Completeness (30%): Covers all key points
- Clarity (20%): Well-explained
- Examples (10%): Provides examples

Return ONLY a JSON object:
{
    "score": 0.0-1.0,
    "feedback": "Detailed feedback in Mongolian",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"]
}"""

        prompt = f"""Question: {question['question_text']}

Expected Answer/Key Points: {question.get('explanation', 'N/A')}

Student's Answer:
{student_answer}

Grade this answer according to the rubric. Be fair and constructive."""

        try:
            response = await self.llm.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=1000,
            )

            # Parse JSON response
            response_text = response.content.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            if response_text.startswith("```"):
                response_text = response_text[3:-3]

            result = json.loads(response_text)
            score_ratio = result.get("score", 0.0)
            points_earned = score_ratio * question["points"]
            is_correct = score_ratio >= 0.7  # 70% threshold

            feedback = result.get("feedback", "")

            return QuestionResult(
                question_id=question["question_id"],
                student_answer=student_answer,
                correct_answer=reference_answer or "(Эссэ - тайлбарыг үзнэ үү)",
                is_correct=is_correct,
                points_earned=points_earned,
                max_points=question["points"],
                feedback=feedback,
            )

        except Exception as e:
            # Fallback: partial credit
            points_earned = question["points"] * 0.5
            return QuestionResult(
                question_id=question["question_id"],
                student_answer=student_answer,
                correct_answer=reference_answer or "(Эссэ - AI үнэлгээ хийгдсэнгүй)",
                is_correct=False,
                points_earned=points_earned,
                max_points=question["points"],
                feedback=f"AI grading unavailable. Partial credit given. Error: {str(e)}",
            )

    def _identify_weak_topics(
        self, results: List[QuestionResult], questions: List[Dict]
    ) -> List[str]:
        """Identify topics where student is weak."""
        # Group by bloom level
        topic_performance = {}

        for result, question in zip(results, questions):
            topic = question.get("bloom_level", "general")

            if topic not in topic_performance:
                topic_performance[topic] = {"correct": 0, "total": 0}

            topic_performance[topic]["total"] += 1
            if result.is_correct:
                topic_performance[topic]["correct"] += 1

        # Identify weak topics (< 60% accuracy)
        weak_topics = []
        for topic, stats in topic_performance.items():
            accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            if accuracy < 0.6:
                weak_topics.append(topic)

        return weak_topics

    def _generate_analytics(
        self, results: List[QuestionResult], questions: List[Dict]
    ) -> Dict:
        """Generate performance analytics."""
        total = len(results)
        correct = sum(1 for r in results if r.is_correct)

        # By difficulty
        by_difficulty = {}
        for result, question in zip(results, questions):
            diff = question.get("difficulty", "medium")
            if diff not in by_difficulty:
                by_difficulty[diff] = {"correct": 0, "total": 0}
            by_difficulty[diff]["total"] += 1
            if result.is_correct:
                by_difficulty[diff]["correct"] += 1

        # By type
        by_type = {}
        for result, question in zip(results, questions):
            qtype = question.get("type", "unknown")
            if qtype not in by_type:
                by_type[qtype] = {"correct": 0, "total": 0}
            by_type[qtype]["total"] += 1
            if result.is_correct:
                by_type[qtype]["correct"] += 1

        return {
            "overall_accuracy": correct / total if total > 0 else 0,
            "by_difficulty": by_difficulty,
            "by_type": by_type,
        }

    async def _generate_overall_feedback(
        self, percentage: float, weak_topics: List[str], analytics: Dict
    ) -> str:
        """Generate overall feedback using AI."""
        system_prompt = """You are an encouraging educational assistant.
Provide constructive, motivating feedback based on test performance.
Be specific, actionable, and encouraging.
Write in Mongolian."""

        prompt = f"""Test Performance:
- Score: {percentage:.1f}%
- Weak topics: {', '.join(weak_topics) if weak_topics else 'None'}
- Analytics: {analytics}

Generate encouraging, constructive feedback (3-5 sentences) in Mongolian."""

        try:
            response = await self.llm.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=300,
            )
            return response.content.strip()
        except:
            # Fallback
            if percentage >= 90:
                return "Маш сайн үр дүн! Та материалыг сайн эзэмшсэн байна."
            elif percentage >= 70:
                return "Сайн үр дүн. Зарим сэдвүүдийг илүү анхааралтай судлаарай."
            else:
                return "Материалыг дахин судлах шаардлагатай. Зарим сэдвүүд сул байна."
