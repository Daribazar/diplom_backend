"""Lecture comprehension agent."""
from typing import Dict, Any
import json

from src.domain.agents.base_agent import BaseAgent
from src.domain.interfaces.llm_adapter import ILLMAdapter


class LectureComprehensionAgent(BaseAgent):
    """Agent for understanding and analyzing lecture content."""
    
    def __init__(self, llm_adapter: ILLMAdapter):
        """
        Initialize lecture comprehension agent.
        
        Args:
            llm_adapter: LLM adapter for text generation
        """
        super().__init__(llm_adapter)
    
    async def execute(self, content: str, title: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze lecture content and extract key concepts.
        
        Args:
            content: Lecture text content
            title: Lecture title
            **kwargs: Additional parameters
            
        Returns:
            Dict with key_concepts and summary
        """
        system_prompt = """You are an expert educational content analyzer.
Your task is to analyze lecture content and extract key concepts that students should learn.

Return your response as valid JSON with this structure:
{
    "key_concepts": ["concept1", "concept2", ...],
    "summary": "Brief summary of the lecture"
}

Guidelines:
- Extract 5-10 key concepts
- Concepts should be specific and actionable
- Summary should be 2-3 sentences
- Focus on what students need to understand"""
        
        user_prompt = f"""Analyze this lecture:

Title: {title}

Content:
{content[:3000]}

Extract the key concepts and provide a summary."""
        
        response = await self.llm_adapter.complete(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Parse JSON response
        try:
            result = json.loads(response.content)
            return {
                "key_concepts": result.get("key_concepts", []),
                "summary": result.get("summary", ""),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except json.JSONDecodeError:
            return {
                "key_concepts": ["Unable to extract concepts"],
                "summary": response.content[:200],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

