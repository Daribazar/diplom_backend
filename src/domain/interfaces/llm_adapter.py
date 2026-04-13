"""LLM adapter interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class LLMUsage:
    """LLM token usage."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class LLMResponse:
    """Standardized LLM response."""

    content: str
    model: str
    usage: LLMUsage
    finish_reason: str


class ILLMAdapter(ABC):
    """LLM adapter interface - domain layer."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate completion.

        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature (0-2)
            max_tokens: Max completion tokens
            **kwargs: Additional provider-specific parameters

        Returns:
            Standardized LLMResponse
        """
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass
