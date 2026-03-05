"""Agent orchestrator for coordinating multiple AI agents."""
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from src.3_domain.agents.lecture_comprehension_agent import LectureComprehensionAgent
from src.3_domain.memory.memory_manager import MemoryManager
from src.4_infrastructure.external.llm.llm_factory import LLMFactory
from src.3_domain.services.chunking.semantic_chunker import SemanticChunker
from src.3_domain.services.embedding.embedding_service import EmbeddingService
from src.4_infrastructure.database.repositories.embedding_repository import EmbeddingRepository
from src.4_infrastructure.database.repositories.lecture_repository import LectureRepository


class AgentOrchestrator:
    """Orchestrates multiple AI agents for complex workflows."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize orchestrator.
        
        Args:
            db: Database session
        """
        self.db = db
        
        # Initialize LLM adapters
        self.llm_adapter = LLMFactory.create_default_adapter()
        self.embedding_adapter = LLMFactory.create_embedding_adapter()
        
        # Initialize services
        self.chunker = SemanticChunker(chunk_size=1000, overlap=200)
        self.embedding_service = EmbeddingService(self.embedding_adapter)
        
        # Initialize repositories
        self.embedding_repo = EmbeddingRepository(db)
        self.lecture_repo = LectureRepository(db)
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            chunker=self.chunker,
            embedding_service=self.embedding_service,
            embedding_repo=self.embedding_repo
        )
        
        # Initialize agents
        self.comprehension_agent = LectureComprehensionAgent(self.llm_adapter)
    
    async def process_lecture(
        self,
        lecture_id: str,
        content: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Process lecture through AI pipeline.
        
        Args:
            lecture_id: Lecture ID
            content: Lecture text content
            title: Lecture title
            
        Returns:
            Processing results with key_concepts and embedding_ids
        """
        # Step 1: Extract key concepts using comprehension agent
        analysis = await self.comprehension_agent.execute(
            content=content,
            title=title
        )
        
        # Step 2: Store lecture content as embeddings
        embedding_ids = await self.memory_manager.store_lecture_memory(
            lecture_id=lecture_id,
            content=content
        )
        
        # Step 3: Update lecture in database
        db_lecture = await self.lecture_repo.get_by_id(lecture_id)
        if db_lecture:
            db_lecture.status = "completed"
            db_lecture.content = content
            db_lecture.key_concepts = analysis["key_concepts"]
            db_lecture.embedding_ids = embedding_ids
            await self.db.commit()
        
        return {
            "lecture_id": lecture_id,
            "key_concepts": analysis["key_concepts"],
            "summary": analysis["summary"],
            "embedding_ids": embedding_ids,
            "chunks_created": len(embedding_ids),
            "llm_usage": analysis["usage"]
        }
    
    async def orchestrate_test_generation(self, lecture_id: int) -> dict:
        """Orchestrate test generation workflow."""
        # TODO: Implement in Phase 7
        raise NotImplementedError()

