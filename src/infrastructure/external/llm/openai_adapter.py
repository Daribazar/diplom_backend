"""OpenAI LLM adapter."""
from typing import Optional, List
from openai import AsyncOpenAI

from src.domain.interfaces.llm_adapter import (
    ILLMAdapter,
    LLMResponse,
    LLMUsage
)
from src.config import settings


class OpenAIAdapter(ILLMAdapter):
    """OpenAI API adapter."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI adapter."""
        self.client = AsyncOpenAI(
            api_key=api_key or settings.OPENAI_API_KEY
        )
        self.default_model = "gpt-4"
        self.embedding_model = "text-embedding-3-small"
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion using OpenAI API.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature (0-2)
            max_tokens: Max completion tokens
            model: Model name (default: gpt-4)
            **kwargs: Additional OpenAI parameters
            
        Returns:
            Standardized LLMResponse
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        try:
            response = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage=LLMUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens
                ),
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings using OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            1536-dimensional vector
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            raise RuntimeError(f"OpenAI embedding error: {str(e)}")
