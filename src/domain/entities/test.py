"""Test domain entity."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict


@dataclass
class Test:
    """Test domain entity."""
    id: str
    lecture_id: str
    title: str
    difficulty: str
    total_points: int
    time_limit: int  # minutes
    questions: List[Dict]
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

