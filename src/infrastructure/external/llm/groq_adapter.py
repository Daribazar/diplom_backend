"""Groq LLM adapter (OpenAI-compatible API)."""

from typing import Optional, List
from openai import AsyncOpenAI

from src.domain.interfaces.llm_adapter import ILLMAdapter, LLMResponse, LLMUsage
from src.config import settings


class GroqAdapter(ILLMAdapter):
    """Groq API adapter using OpenAI-compatible endpoint.

    Groq provides a free tier with high rate limits for Llama models.
    Get an API key at https://console.groq.com/keys
    """

    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = AsyncOpenAI(
            api_key=api_key or settings.GROQ_API_KEY,
            base_url=self.BASE_URL,
        )
        self.default_model = model or "llama-3.3-70b-versatile"

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        model: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage=LLMUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                ),
                finish_reason=response.choices[0].finish_reason,
            )
        except Exception as e:
            raise RuntimeError(f"Groq API error: {str(e)}")

    async def embed(self, text: str) -> List[float]:
        """Groq does not provide embeddings — caller should use a different adapter."""
        raise NotImplementedError(
            "Groq does not provide embeddings. Use mock or OpenAI for embeddings."
        )
