"""Embedding database model."""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector

from src.infrastructure.database.models.base import Base, TimestampMixin


class LectureEmbedding(Base, TimestampMixin):
    """Lecture chunk embeddings for RAG."""
    
    __tablename__ = "lecture_embeddings"
    
    id = Column(String, primary_key=True)
    lecture_id = Column(String, ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=False)  # OpenAI embedding dimension
    
    def __repr__(self) -> str:
        return f"<LectureEmbedding {self.id} lecture={self.lecture_id} chunk={self.chunk_index}>"
