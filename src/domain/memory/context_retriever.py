"""Context retrieval for RAG."""
from typing import List, Dict, Any
from src.domain.memory.memory_manager import MemoryManager


class ContextRetriever:
    """Retrieves relevant context for agent queries."""
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize context retriever.
        
        Args:
            memory_manager: Memory manager instance
        """
        self.memory_manager = memory_manager
    
    async def retrieve_for_test_generation(
        self,
        lecture_ids: List[str],
        topic: str,
        top_k: int = 5
    ) -> str:
        """
        Retrieve context for test generation.
        
        Args:
            lecture_ids: Lecture IDs to search
            topic: Test topic/query
            top_k: Number of chunks to retrieve
            
        Returns:
            Formatted context string
        """
        context_chunks = await self.memory_manager.retrieve_relevant_context(
            query=topic,
            lecture_ids=lecture_ids,
            top_k=top_k
        )
        
        # Format context
        context_parts = []
        for chunk in context_chunks:
            context_parts.append(
                f"[Lecture {chunk['lecture_id']} - Chunk {chunk['chunk_index']}]\n"
                f"{chunk['text']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    async def retrieve_for_evaluation(
        self,
        lecture_ids: List[str],
        question: str,
        student_answer: str,
        top_k: int = 3
    ) -> str:
        """
        Retrieve context for answer evaluation.
        
        Args:
            lecture_ids: Lecture IDs to search
            question: Test question
            student_answer: Student's answer
            top_k: Number of chunks
            
        Returns:
            Formatted context string
        """
        # Combine question and answer for better retrieval
        query = f"{question}\n{student_answer}"
        
        context_chunks = await self.memory_manager.retrieve_relevant_context(
            query=query,
            lecture_ids=lecture_ids,
            top_k=top_k
        )
        
        # Format context
        context_parts = []
        for chunk in context_chunks:
            context_parts.append(chunk['text'])
        
        return "\n\n".join(context_parts)
