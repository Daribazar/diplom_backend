"""Embedding generation service."""
from typing import List
from src.domain.interfaces.llm_adapter import ILLMAdapter


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self, llm_adapter: ILLMAdapter):
        """
        Initialize embedding service.
        
        Args:
            llm_adapter: LLM adapter with embedding support
        """
        self.llm_adapter = llm_adapter
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return await self.llm_adapter.embed(text)
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
