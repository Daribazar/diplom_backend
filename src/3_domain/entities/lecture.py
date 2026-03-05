"""Lecture domain entity."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Lecture:
    """Lecture domain entity with business logic."""
    
    id: str
    course_id: str
    week_number: int
    title: str
    status: str = "pending"
    content: Optional[str] = None
    file_url: Optional[str] = None
    key_concepts: List[str] = field(default_factory=list)
    embedding_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    
    def is_processed(self) -> bool:
        """Business rule: Check if lecture is fully processed."""
        return self.status == "completed" and len(self.embedding_ids) > 0
    
    def is_ready_for_test_generation(self) -> bool:
        """Business rule: Ready for test generation."""
        return self.is_processed() and len(self.key_concepts) >= 3
    
    def mark_as_processing(self) -> None:
        """State transition: pending → processing."""
        if self.status != "pending":
            raise ValueError(f"Cannot process lecture in '{self.status}' state")
        self.status = "processing"
    
    def mark_as_completed(
        self,
        content: str,
        key_concepts: List[str],
        embedding_ids: List[str]
    ) -> None:
        """State transition: processing → completed."""
        if self.status != "processing":
            raise ValueError(f"Cannot complete lecture in '{self.status}' state")
        if len(content) < 100:
            raise ValueError("Content too short (min 100 chars)")
        if len(key_concepts) < 1:
            raise ValueError("At least 1 key concept required")
        if len(embedding_ids) < 1:
            raise ValueError("At least 1 embedding required")
        
        self.content = content
        self.key_concepts = key_concepts
        self.embedding_ids = embedding_ids
        self.status = "completed"
        self.processed_at = datetime.utcnow()
