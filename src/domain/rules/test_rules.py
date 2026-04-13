"""Test generation and validation rules."""


class TestRules:
    """Business rules for test generation."""

    MIN_QUESTIONS = 1
    MAX_QUESTIONS = 50
    DEFAULT_QUESTIONS = 10

    DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

    @staticmethod
    def validate_question_count(count: int) -> bool:
        """Validate question count."""
        return TestRules.MIN_QUESTIONS <= count <= TestRules.MAX_QUESTIONS

    @staticmethod
    def validate_difficulty(difficulty: str) -> bool:
        """Validate difficulty level."""
        return difficulty.lower() in TestRules.DIFFICULTY_LEVELS
