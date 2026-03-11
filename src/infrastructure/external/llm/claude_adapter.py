"""Anthropic Claude LLM adapter."""
from typing import Optional, List
from anthropic import AsyncAnthropic

from src.domain.interfaces.llm_adapter import (
    ILLMAdapter,
    LLMResponse,
    LLMUsage
)
from src.config import settings


class ClaudeAdapter(ILLMAdapter):
    """Anthropic Claude API adapter."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude adapter."""
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.default_model = "claude-sonnet-4-20250514"
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using Claude API.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature (0-1)
            max_tokens: Max completion tokens
            model: Model name
            **kwargs: Additional Claude parameters
            
        Returns:
            Standardized LLMResponse
        """
        try:
            # Create client for each request to avoid async issues
            client = AsyncAnthropic(api_key=self.api_key)
            
            response = await client.messages.create(
                model=model or self.default_model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt or "You are a helpful assistant.",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                **kwargs
            )
            
            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                usage=LLMUsage(
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens
                ),
                finish_reason=response.stop_reason
            )
            
        except Exception as e:
            raise RuntimeError(f"Claude API error: {str(e)}")
    
    async def embed(self, text: str) -> List[float]:
        """
        Claude doesn't provide embeddings.
        Use OpenAI for embeddings even with Claude.
        """
        raise NotImplementedError(
            "Claude doesn't provide embeddings. Use OpenAI adapter."
        )
