"""Mock LLM adapter for testing without API keys."""
from typing import Optional, List
import json

from src.domain.interfaces.llm_adapter import (
    ILLMAdapter,
    LLMResponse,
    LLMUsage
)


class MockLLMAdapter(ILLMAdapter):
    """Mock LLM adapter for testing."""
    
    def __init__(self):
        """Initialize mock adapter."""
        self.call_count = 0
    
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
        Generate mock completion.
        
        Returns realistic mock responses based on prompt content.
        """
        self.call_count += 1
        
        # Detect what kind of response is needed
        prompt_lower = prompt.lower()
        
        if "key concept" in prompt_lower or "extract" in prompt_lower:
            content = json.dumps({
                "key_concepts": [
                    "Neural Networks",
                    "Backpropagation",
                    "Activation Functions",
                    "Deep Learning",
                    "Machine Learning"
                ],
                "summary": "This lecture covers the fundamentals of neural networks, including their architecture, learning mechanisms, and applications in modern AI systems."
            })
        
        elif "generate" in prompt_lower and "question" in prompt_lower:
            content = json.dumps({
                "mcq": [
                    {
                        "question": "What is a neural network?",
                        "options": [
                            "A biological system",
                            "A computing system inspired by biological neural networks",
                            "A type of database",
                            "A programming language"
                        ],
                        "correct_answer": "B",
                        "explanation": "Neural networks are computing systems inspired by biological neural networks."
                    }
                ],
                "true_false": [
                    {
                        "question": "Neural networks can learn from data.",
                        "correct_answer": "True",
                        "explanation": "Neural networks use training data to adjust their weights and improve performance."
                    }
                ],
                "essay": [
                    {
                        "question": "Explain how backpropagation works in neural networks.",
                        "key_points": [
                            "Forward pass computation",
                            "Error calculation",
                            "Gradient computation",
                            "Weight updates"
                        ]
                    }
                ]
            })
        
        elif "evaluate" in prompt_lower or "score" in prompt_lower:
            content = json.dumps({
                "score": 8,
                "max_points": 10,
                "feedback": "Good answer! You demonstrated understanding of the key concepts. Consider adding more details about the gradient descent process.",
                "strengths": [
                    "Clear explanation",
                    "Correct terminology"
                ],
                "improvements": [
                    "Add more technical details",
                    "Include examples"
                ]
            })
        
        else:
            # Generic response
            content = "This is a mock response from the LLM adapter. In production, this would be a real AI-generated response."
        
        return LLMResponse(
            content=content,
            model="mock-model-v1",
            usage=LLMUsage(
                prompt_tokens=len(prompt.split()),
                completion_tokens=len(content.split()),
                total_tokens=len(prompt.split()) + len(content.split())
            ),
            finish_reason="stop"
        )
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate mock embeddings.
        
        Returns a 1536-dimensional vector (same as OpenAI).
        """
        # Generate deterministic but varied embeddings based on text
        import hashlib
        
        # Use hash of text to generate consistent embeddings
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Convert hash to numbers and normalize
        embeddings = []
        for i in range(0, len(text_hash), 2):
            val = int(text_hash[i:i+2], 16) / 255.0  # Normalize to 0-1
            embeddings.append(val * 2 - 1)  # Scale to -1 to 1
        
        # Pad to 1536 dimensions
        while len(embeddings) < 1536:
            embeddings.extend(embeddings[:min(16, 1536 - len(embeddings))])
        
        return embeddings[:1536]
