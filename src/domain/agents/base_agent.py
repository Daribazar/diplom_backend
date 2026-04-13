"""Base agent class."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Base class for all AI agents."""

    def __init__(self, llm_adapter):
        """Initialize agent with LLM adapter."""
        self.llm_adapter = llm_adapter

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute agent task."""
        pass
