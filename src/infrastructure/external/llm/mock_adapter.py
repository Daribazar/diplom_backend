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
            # Generate questions in the format expected by test_generator_agent
            content = json.dumps({
                "questions": [
                    {
                        "question_id": "q1",
                        "type": "mcq",
                        "question_text": "Нейрон сүлжээ гэж юу вэ?",
                        "options": [
                            "Биологийн систем",
                            "Биологийн нейрон сүлжээнээс санаа авсан тооцооллын систем",
                            "Өгөгдлийн сангийн төрөл",
                            "Программчлалын хэл"
                        ],
                        "correct_answer": "Биологийн нейрон сүлжээнээс санаа авсан тооцооллын систем",
                        "points": 2,
                        "difficulty": "easy",
                        "bloom_level": "remember",
                        "explanation": "Нейрон сүлжээ нь биологийн нейрон сүлжээнээс санаа авсан тооцооллын систем юм."
                    },
                    {
                        "question_id": "q2",
                        "type": "mcq",
                        "question_text": "Нейрон сүлжээний үндсэн бүрэлдэхүүн хэсэг юу вэ?",
                        "options": [
                            "Нейрон (node)",
                            "Холболт (connection)",
                            "Жин (weight)",
                            "Бүгд зөв"
                        ],
                        "correct_answer": "Бүгд зөв",
                        "points": 2,
                        "difficulty": "medium",
                        "bloom_level": "understand",
                        "explanation": "Нейрон сүлжээ нь нейрон, холболт, жингээс бүрдэнэ."
                    },
                    {
                        "question_id": "q3",
                        "type": "true_false",
                        "question_text": "Нейрон сүлжээ өгөгдлөөс суралцах чадвартай.",
                        "options": ["Үнэн", "Худал"],
                        "correct_answer": "Үнэн",
                        "points": 1,
                        "difficulty": "easy",
                        "bloom_level": "remember",
                        "explanation": "Нейрон сүлжээ сургалтын өгөгдлийг ашиглан жингээ тохируулж, гүйцэтгэлээ сайжруулдаг."
                    },
                    {
                        "question_id": "q4",
                        "type": "mcq",
                        "question_text": "Activation function-ий үүрэг юу вэ?",
                        "options": [
                            "Өгөгдлийг хадгалах",
                            "Нейроны гаралтыг тооцоолох",
                            "Сүлжээг сургах",
                            "Алдааг тооцоолох"
                        ],
                        "correct_answer": "Нейроны гаралтыг тооцоолох",
                        "points": 2,
                        "difficulty": "medium",
                        "bloom_level": "apply",
                        "explanation": "Activation function нь нейроны оролтыг боловсруулж гаралт үүсгэдэг."
                    },
                    {
                        "question_id": "q5",
                        "type": "mcq",
                        "question_text": "Backpropagation алгоритм юу хийдэг вэ?",
                        "options": [
                            "Өгөгдлийг урьдчилан таамаглах",
                            "Алдааг буцааж дамжуулж жингийг шинэчлэх",
                            "Өгөгдлийг цэвэрлэх",
                            "Сүлжээний бүтцийг өөрчлөх"
                        ],
                        "correct_answer": "Алдааг буцааж дамжуулж жингийг шинэчлэх",
                        "points": 3,
                        "difficulty": "hard",
                        "bloom_level": "analyze",
                        "explanation": "Backpropagation нь алдааг буцааж дамжуулж gradient тооцоолон жингийг шинэчилдэг."
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
