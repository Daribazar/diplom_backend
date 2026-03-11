"""Memory manager for agents."""
from typing import List, Dict, Any
from src.domain.services.chunking.semantic_chunker import SemanticChunker
from src.domain.services.embedding.embedding_service import EmbeddingService
from src.infrastructure.database.repositories.embedding_repository import EmbeddingRepository


class MemoryManager:
    """Manages agent memory and context."""
    
    def __init__(
        self,
        chunker: SemanticChunker,
        embedding_service: EmbeddingService,
        embedding_repo: EmbeddingRepository
    ):
        """
        Initialize memory manager.
        
        Args:
            chunker: Text chunking service
            embedding_service: Embedding generation service
            embedding_repo: Embedding repository
        """
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.embedding_repo = embedding_repo
    
    async def store_lecture_memory(
        self,
        lecture_id: str,
        content: str
    ) -> List[str]:
        """
        Store lecture content as embeddings.
        
        Args:
            lecture_id: Lecture ID
            content: Lecture text content
            
        Returns:
            List of created embedding IDs
        """
        # Chunk text
        chunks = await self.chunker.chunk_text(content)
        
        # Generate embeddings
        embeddings = await self.embedding_service.generate_embeddings(chunks)
        
        # Store in database
        embedding_ids = await self.embedding_repo.create_batch(
            lecture_id=lecture_id,
            chunks=chunks,
            embeddings=embeddings
        )
        
        return embedding_ids
    
    async def retrieve_relevant_context(
        self,
        query: str,
        lecture_ids: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for query.
        
        Args:
            query: Search query
            lecture_ids: Filter by lecture IDs
            top_k: Number of results
            
        Returns:
            List of relevant chunks with metadata
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.generate_embedding(query)
        
        # Search similar embeddings
        results = await self.embedding_repo.search_similar(
            query_embedding=query_embedding,
            lecture_ids=lecture_ids,
            limit=top_k
        )
        
        # Format results
        context = []
        for result in results:
            context.append({
                "lecture_id": result.lecture_id,
                "chunk_index": result.chunk_index,
                "text": result.chunk_text,
                "embedding_id": result.id
            })
        
        return context
