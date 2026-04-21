"""Embedding generation service."""

from typing import List

from src.domain.interfaces.llm_adapter import ILLMAdapter


class EmbeddingService:
    """Generate text embeddings via an LLM adapter."""

    def __init__(self, llm_adapter: ILLMAdapter):
        self.llm_adapter = llm_adapter

    async def generate_embedding(self, text: str) -> List[float]:
        """Embed a single text."""
        return await self.llm_adapter.embed(text)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Embed many texts sequentially."""
        return [await self.generate_embedding(text) for text in texts]
