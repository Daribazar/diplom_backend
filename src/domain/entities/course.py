"""Course domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Course:
    """Course domain entity."""

    id: str
    name: str
    code: str
    semester: str
    owner_id: str
    instructor: Optional[str] = None
    color: str = "indigo"
    created_at: Optional[datetime] = None

    def update_instructor(self, instructor_name: str) -> None:
        """Business rule: Update instructor."""
        self.instructor = instructor_name
