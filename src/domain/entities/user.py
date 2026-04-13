"""User domain entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User domain entity - pure business logic."""

    id: str
    email: str
    full_name: str
    is_active: bool = True
    role: str = "student"
    created_at: Optional[datetime] = None

    def deactivate(self) -> None:
        """Business rule: Deactivate user."""
        self.is_active = False

    def activate(self) -> None:
        """Business rule: Activate user."""
        self.is_active = True
