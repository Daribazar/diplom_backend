"""Base LLM adapter."""
from abc import ABC
from src.3_domain.interfaces.llm_adapter import ILLMAdapter


class BaseLLMAdapter(ILLMAdapter, ABC):
    """Base implementation for LLM adapters."""
    
    def __init__(self, api_key: str, model: str):
        """Initialize adapter."""
        self.api_key = api_key
        self.model = model
