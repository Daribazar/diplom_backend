"""LLM adapter factory."""

from typing import Optional
from src.infrastructure.external.llm.openai_adapter import OpenAIAdapter
from src.infrastructure.external.llm.claude_adapter import ClaudeAdapter
from src.infrastructure.external.llm.groq_adapter import GroqAdapter
from src.infrastructure.external.llm.mock_adapter import MockLLMAdapter
from src.domain.interfaces.llm_adapter import ILLMAdapter
from src.config import settings


class LLMFactory:
    """Factory for creating LLM adapters."""

    @staticmethod
    def create_openai_adapter(api_key: Optional[str] = None) -> ILLMAdapter:
        """Create OpenAI adapter."""
        return OpenAIAdapter(api_key=api_key)

    @staticmethod
    def create_claude_adapter(api_key: Optional[str] = None) -> ILLMAdapter:
        """Create Claude adapter."""
        return ClaudeAdapter(api_key=api_key)

    @staticmethod
    def create_groq_adapter(api_key: Optional[str] = None) -> ILLMAdapter:
        """Create Groq adapter (OpenAI-compatible, free tier)."""
        return GroqAdapter(api_key=api_key)

    @staticmethod
    def create_mock_adapter() -> ILLMAdapter:
        """Create mock adapter for testing."""
        return MockLLMAdapter()

    @staticmethod
    def create_default_adapter() -> ILLMAdapter:
        """Create default adapter based on settings."""
        provider = getattr(settings, "DEFAULT_LLM_PROVIDER", "openai").lower()

        if provider == "mock":
            return LLMFactory.create_mock_adapter()
        elif provider == "claude":
            return LLMFactory.create_claude_adapter()
        elif provider == "groq":
            return LLMFactory.create_groq_adapter()
        else:
            return LLMFactory.create_openai_adapter()

    @staticmethod
    def create_embedding_adapter() -> ILLMAdapter:
        """
        Create adapter for embeddings.

        Groq/Claude/Mock providers don't support embeddings, so we fall back to
        a mock embedding adapter. Use OpenAI for real embeddings.
        """
        provider = getattr(settings, "DEFAULT_LLM_PROVIDER", "openai").lower()

        if provider in ["mock", "claude", "groq"]:
            return MockLLMAdapter()

        return OpenAIAdapter()
