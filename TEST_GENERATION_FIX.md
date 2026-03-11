# Test Generation Fix - Questions Empty Issue

## Problem
Tests were being created successfully (201 Created), but the `questions` array was empty in the database. This caused errors on the frontend when trying to take tests:
```
Cannot read properties of undefined (reading 'points')
```

## Root Cause
The MockLLMAdapter was returning the wrong JSON format for test generation. The TestGeneratorAgent expects a specific format with a `questions` array, but the mock was returning separate arrays for different question types.

**Wrong format (old):**
```json
{
  "mcq": [...],
  "true_false": [...],
  "essay": [...]
}
```

**Correct format (new):**
```json
{
  "questions": [
    {
      "question_id": "q1",
      "type": "mcq",
      "question_text": "...",
      "options": [...],
      "correct_answer": "...",
      "points": 2,
      "difficulty": "easy",
      "bloom_level": "remember",
      "explanation": "..."
    }
  ]
}
```

## Changes Made

### 1. Fixed MockLLMAdapter (`src/infrastructure/external/llm/mock_adapter.py`)
- ✅ Updated the mock response format to match what TestGeneratorAgent expects
- ✅ Changed from separate arrays (mcq, true_false, essay) to unified questions array
- ✅ Added 5 sample questions in Mongolian language
- ✅ Each question now has all required fields: question_id, type, question_text, options, correct_answer, points, difficulty, bloom_level, explanation
- ✅ Questions cover different difficulty levels (easy, medium, hard) and Bloom's taxonomy levels

### 2. Improved Error Handling in TestGeneratorAgent (`src/domain/agents/test_generator_agent.py`)
- ✅ Added logging to track context retrieval length
- ✅ Added fallback context if RAG returns empty results (prevents ValueError)
- ✅ Added detailed logging in `_parse_questions()` to debug JSON parsing
- ✅ Added try-catch for individual question parsing to prevent one bad question from breaking all
- ✅ Log first 200 chars of LLM response for debugging
- ✅ Log number of questions parsed and created

### 3. Added Logging to GenerateTestUseCase (`src/application/usecases/test/generate_test.py`)
- ✅ Log when test generation starts with lecture ID
- ✅ Log parameters (difficulty, question types, count)
- ✅ Log number of questions generated
- ✅ Log total points calculated

### 4. Added Logging to TestRepository (`src/infrastructure/database/repositories/test_repository.py`)
- ✅ Log when creating test with test ID
- ✅ Log questions count before saving
- ✅ Log first 2 questions data for verification
- ✅ Log questions count after saving from database

## Testing Instructions

### 1. Restart Backend
```bash
cd study-assistant-backend
source venv/bin/activate
uvicorn src.main:app --reload
```

### 2. Upload a Lecture (if not already done)
- Go to http://localhost:3000/courses/[courseId]/lectures/upload
- Upload a PDF file
- Wait for processing to complete (status: "completed")

### 3. Generate a Test
- Go to http://localhost:3000/courses/[courseId]/tests/generate
- Fill in the form:
  - Week number: 1
  - Number of MCQ: 3
  - Number of True/False: 2
  - Difficulty: medium
- Click "Тест үүсгэх" (Generate Test)

### 4. Check Backend Logs
You should see output like:
```
[GenerateTestUseCase] Generating test for lecture lec_xxx
[GenerateTestUseCase] Parameters: difficulty=Difficulty.MEDIUM, types=[QuestionType.MCQ, QuestionType.TRUE_FALSE], count=5
[TestGenerator] Retrieved context length: 1234
[TestGenerator] Parsing LLM response (first 200 chars): {"questions": [{"question_id": "q1", "type": "mcq"...
[TestGenerator] Parsed 5 questions from LLM response
[TestGenerator] Successfully created 5 Question objects
[GenerateTestUseCase] Generated 5 questions
[GenerateTestUseCase] Total points: 10
[TestRepository] Creating test test_xxx
[TestRepository] Questions count: 5
[TestRepository] Questions data: [{'question_id': 'q1', 'type': 'mcq'...
[TestRepository] Test saved. DB questions count: 5
```

### 5. Verify in Database
```sql
SELECT 
  id, 
  title, 
  total_points,
  jsonb_array_length(questions) as question_count,
  questions->0->>'question_text' as first_question
FROM tests 
ORDER BY created_at DESC 
LIMIT 1;
```

Expected result:
```
id              | title                    | total_points | question_count | first_question
test_xxx        | Week 1 Test - Medium     | 10           | 5              | Нейрон сүлжээ гэж юу вэ?
```

### 6. Take the Test
- Go to http://localhost:3000/courses/[courseId]/tests/[testId]/take
- Questions should now display properly
- You should see 5 questions in Mongolian
- No more "Cannot read properties of undefined" errors

## Expected Behavior After Fix

✅ Tests are created with 5 questions (or the requested number)  
✅ Questions are stored in the database JSONB column  
✅ Questions display properly on the test taking page  
✅ No more "Cannot read properties of undefined" errors  
✅ Questions are in Mongolian language  
✅ Questions have proper difficulty levels and Bloom's taxonomy levels  
✅ Backend logs show detailed information about test generation process  

## Sample Questions Generated

The mock adapter now generates these 5 questions:

1. **MCQ (Easy)**: Нейрон сүлжээ гэж юу вэ? (What is a neural network?)
2. **MCQ (Medium)**: Нейрон сүлжээний үндсэн бүрэлдэхүүн хэсэг юу вэ? (What are the basic components?)
3. **True/False (Easy)**: Нейрон сүлжээ өгөгдлөөс суралцах чадвартай. (Neural networks can learn from data)
4. **MCQ (Medium)**: Activation function-ий үүрэг юу вэ? (What is the role of activation function?)
5. **MCQ (Hard)**: Backpropagation алгоритм юу хийдэг вэ? (What does backpropagation do?)

## Notes

- ✅ The fix uses mock data since `DEFAULT_LLM_PROVIDER=mock` in `.env`
- ✅ For production, switch to `openai` or `claude` provider in `.env`
- ✅ **RECOMMENDED: Use Claude for better quality questions** - See `CLAUDE_TEST_GENERATION.md`
- ✅ The mock questions are in Mongolian language to match the UI
- ✅ If RAG context is empty (no embeddings), it uses fallback context to still generate questions
- ✅ All logging uses `[ComponentName]` prefix for easy filtering
- ✅ Frontend already has proper error handling for empty questions

## Using Claude for Production

To use Claude instead of mock:

1. Update `.env`:
```bash
DEFAULT_LLM_PROVIDER=claude
```

2. Verify API key:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-...
```

3. Restart backend:
```bash
uvicorn src.main:app --reload
```

Claude will generate:
- ✅ Higher quality questions based on actual lecture content
- ✅ Questions in Mongolian language
- ✅ Proper difficulty levels (Bloom's Taxonomy)
- ✅ Detailed explanations
- ✅ Realistic distractors for MCQ

See `CLAUDE_TEST_GENERATION.md` for detailed guide.

## Troubleshooting

If questions are still empty:

1. Check backend logs for errors in test generation
2. Verify lecture status is "completed" before generating test
3. Check if embeddings exist for the lecture in database:
   ```sql
   SELECT COUNT(*) FROM embeddings WHERE lecture_id = 'lec_xxx';
   ```
4. If using real LLM (not mock), check API keys in `.env`
5. Check if LLM response format matches expected format in logs
