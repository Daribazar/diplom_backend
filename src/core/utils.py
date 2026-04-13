"""Utility functions."""

import uuid
from datetime import datetime


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID (e.g., "user", "course")

    Returns:
        String ID in format: prefix_uuid (e.g., "user_abc123...")
    """
    unique_id = str(uuid.uuid4()).replace("-", "")[:12]
    if prefix:
        return f"{prefix}_{unique_id}"
    return unique_id
