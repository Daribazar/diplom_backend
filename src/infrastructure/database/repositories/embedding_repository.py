"""Embedding repository."""

from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.embedding import LectureEmbedding
from src.core.utils import generate_id


class EmbeddingRepository:
    """Repository for lecture embeddings."""

    def __init__(self, db: AsyncSession):
        """Initialize repository."""
        self.db = db

    async def create(
        self, lecture_id: str, chunk_index: int, chunk_text: str, embedding: List[float]
    ) -> LectureEmbedding:
        """
        Create embedding record.

        Args:
            lecture_id: Lecture ID
            chunk_index: Chunk position
            chunk_text: Text content
            embedding: Vector embedding

        Returns:
            Created embedding
        """
        db_embedding = LectureEmbedding(
            id=generate_id("emb"),
            lecture_id=lecture_id,
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            embedding=embedding,
        )

        self.db.add(db_embedding)
        await self.db.commit()
        await self.db.refresh(db_embedding)

        return db_embedding

    async def create_batch(
        self, lecture_id: str, chunks: List[str], embeddings: List[List[float]]
    ) -> List[str]:
        """
        Create multiple embeddings.

        Args:
            lecture_id: Lecture ID
            chunks: Text chunks
            embeddings: Vector embeddings

        Returns:
            List of created embedding IDs
        """
        embedding_ids = []

        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            db_embedding = LectureEmbedding(
                id=generate_id("emb"),
                lecture_id=lecture_id,
                chunk_index=idx,
                chunk_text=chunk,
                embedding=embedding,
            )
            self.db.add(db_embedding)
            embedding_ids.append(db_embedding.id)

        await self.db.commit()
        return embedding_ids

    async def search_similar(
        self,
        query_embedding: List[float],
        lecture_ids: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[LectureEmbedding]:
        """
        Search similar embeddings using cosine similarity.

        Args:
            query_embedding: Query vector
            lecture_ids: Filter by lecture IDs
            limit: Max results

        Returns:
            Similar embeddings ordered by relevance
        """
        query = select(LectureEmbedding).order_by(
            LectureEmbedding.embedding.cosine_distance(query_embedding)
        )

        if lecture_ids:
            query = query.where(LectureEmbedding.lecture_id.in_(lecture_ids))

        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_lecture(self, lecture_id: str) -> List[LectureEmbedding]:
        """Get all embeddings for a lecture."""
        result = await self.db.execute(
            select(LectureEmbedding)
            .where(LectureEmbedding.lecture_id == lecture_id)
            .order_by(LectureEmbedding.chunk_index)
        )
        return list(result.scalars().all())

    async def delete_by_lecture(self, lecture_id: str) -> None:
        """Delete all embeddings for a lecture."""
        await self.db.execute(
            delete(LectureEmbedding).where(LectureEmbedding.lecture_id == lecture_id)
        )
        await self.db.commit()
