"""Test LLM and AI Agents."""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.infrastructure.external.llm.llm_factory import LLMFactory
from src.domain.agents.lecture_comprehension_agent import LectureComprehensionAgent
from src.domain.agents.test_generator_agent import TestGeneratorAgent
from src.domain.agents.evaluation_agent import EvaluationAgent


async def test_llm_connection():
    """Test basic LLM connection."""
    print("=" * 70)
    print("1. Testing LLM Connection")
    print("=" * 70)
    
    try:
        llm = LLMFactory.create_default_adapter()
        
        # Simple test prompt
        response = await llm.complete(
            prompt="Say 'Hello, I am working!' in one sentence.",
            max_tokens=50
        )
        
        print(f"✅ LLM Response: {response.content}")
        return True
    except Exception as e:
        print(f"❌ LLM Connection Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_lecture_comprehension_agent():
    """Test Lecture Comprehension Agent."""
    print("\n" + "=" * 70)
    print("2. Testing Lecture Comprehension Agent")
    print("=" * 70)
    
    try:
        llm = LLMFactory.create_default_adapter()
        agent = LectureComprehensionAgent(llm)
        
        # Sample lecture content
        content = """
        Introduction to Neural Networks
        
        Neural networks are computing systems inspired by biological neural networks.
        They consist of interconnected nodes (neurons) organized in layers.
        
        Key components:
        1. Input Layer - Receives data
        2. Hidden Layers - Process information
        3. Output Layer - Produces results
        
        Learning happens through backpropagation and gradient descent.
        """
        
        result = await agent.extract_concepts(
            content=content,
            title="Introduction to Neural Networks"
        )
        
        print(f"✅ Key Concepts Extracted: {len(result['key_concepts'])} concepts")
        for concept in result['key_concepts'][:3]:
            print(f"   - {concept}")
        
        print(f"✅ Summary: {result['summary'][:100]}...")
        return True
    except Exception as e:
        print(f"❌ Lecture Comprehension Agent Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_test_generator_agent():
    """Test Test Generator Agent."""
    print("\n" + "=" * 70)
    print("3. Testing Test Generator Agent")
    print("=" * 70)
    
    try:
        llm = LLMFactory.create_default_adapter()
        agent = TestGeneratorAgent(llm)
        
        # Sample context
        context = """
        Neural networks consist of layers of interconnected nodes.
        The input layer receives data, hidden layers process it,
        and the output layer produces results.
        """
        
        result = await agent.generate_questions(
            context=context,
            num_mcq=2,
            num_true_false=1,
            num_essay=1,
            difficulty="medium"
        )
        
        print(f"✅ Questions Generated:")
        print(f"   - MCQ: {len(result['mcq'])} questions")
        print(f"   - True/False: {len(result['true_false'])} questions")
        print(f"   - Essay: {len(result['essay'])} questions")
        
        if result['mcq']:
            print(f"\n   Sample MCQ: {result['mcq'][0]['question'][:80]}...")
        
        return True
    except Exception as e:
        print(f"❌ Test Generator Agent Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_evaluation_agent():
    """Test Evaluation Agent."""
    print("\n" + "=" * 70)
    print("4. Testing Evaluation Agent")
    print("=" * 70)
    
    try:
        llm = LLMFactory.create_default_adapter()
        agent = EvaluationAgent(llm)
        
        # Sample essay question and answer
        question = "Explain how neural networks learn."
        answer = "Neural networks learn through backpropagation and gradient descent."
        correct_answer = "Neural networks learn by adjusting weights through backpropagation."
        
        result = await agent.evaluate_essay(
            question=question,
            student_answer=answer,
            correct_answer=correct_answer,
            max_points=10
        )
        
        print(f"✅ Essay Evaluation:")
        print(f"   - Score: {result['score']}/{result['max_points']}")
        print(f"   - Feedback: {result['feedback'][:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ Evaluation Agent Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("AI AGENTS & LLM TEST SUITE")
    print("=" * 70)
    print("\nMake sure:")
    print("  1. OPENAI_API_KEY is set in .env")
    print("  2. Internet connection is available")
    print("\n")
    
    results = []
    
    # Test 1: LLM Connection
    results.append(await test_llm_connection())
    
    if not results[0]:
        print("\n❌ LLM connection failed. Cannot proceed with agent tests.")
        return
    
    # Test 2: Lecture Comprehension Agent
    results.append(await test_lecture_comprehension_agent())
    
    # Test 3: Test Generator Agent
    results.append(await test_test_generator_agent())
    
    # Test 4: Evaluation Agent
    results.append(await test_evaluation_agent())
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    tests = [
        "LLM Connection",
        "Lecture Comprehension Agent",
        "Test Generator Agent",
        "Evaluation Agent"
    ]
    
    for i, (test_name, result) in enumerate(zip(tests, results), 1):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i}. {test_name}: {status}")
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! AI agents are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")


if __name__ == "__main__":
    asyncio.run(main())
