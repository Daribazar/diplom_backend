"""Student attempt domain entity."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional


@dataclass
class StudentAttempt:
    """Student test attempt entity."""
    id: str
    student_id: str
    test_id: str
    total_score: float = 0.0
    percentage: float = 0.0
    status: str = "in_progress"  # in_progress, submitted, graded
    answers: List[Dict] = field(default_factory=list)
    weak_topics: List[str] = field(default_factory=list)
    analytics: Dict = field(default_factory=dict)
    created_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    
    def calculate_percentage(self, total_points: int):
        """Calculate percentage score."""
        if total_points > 0:
            self.percentage = (self.total_score / total_points) * 100
        else:
            self.percentage = 0.0
    
    def mark_as_submitted(self):
        """Mark attempt as submitted."""
        self.status = "submitted"
        self.submitted_at = datetime.utcnow()
    
    def mark_as_graded(self):
        """Mark attempt as graded."""
        self.status = "graded"

