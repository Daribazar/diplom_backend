# Phase 8: Test Generation with RAG - COMPLETE ✅

## Overview
Implemented AI-powered test generation using RAG (Retrieval-Augmented Generation). The system retrieves relevant lecture content and generates high-quality test questions based on Bloom's Taxonomy.

## Components Implemented

### 1. Test Generator Agent
**File: `src/3_domain/agents/test_generator_agent.py`**

**Features:**
- RAG-based question generation
- Bloom's Taxonomy alignment
- Multiple question types (MCQ, True/False, Essay)
- Difficulty levels (Easy, Medium, Hard)
- Quality validation
- JSON parsing with error handling

**Workflow:**
1. Retrieve context from lecture embeddings (RAG)
2. Generate questions using LLM with context
3. Validate question quality
4. Format and return results

**Question Types:**
- `mcq`: Multiple choice questions
- `true_false`: True/false questions
- `essay`: Essay questions

**Difficulty Levels (Bloom's Taxonomy):**
- `easy`: Remember & Understand (recall facts, explain concepts)
- `medium`: Apply & Analyze (use knowledge, break down problems)
- `hard`: Evaluate & Create (judge, design, synthesize)

### 2. Test Generation Use Case
**File: `src/2_application/usecases/test/generate_test.py`**

**Business Rules:**
- User must own the course
- Lecture must be processed (status: "completed")
- Validates ownership before generation
- Creates test entity with metadata

**Parameters:**
- `course_id`: Course identifier
- `week_number`: Week to generate test for
- `difficulty`: easy/medium/hard
- `question_types`: List of question types
- `question_count`: Number of questions (5-20)

### 3. Test Repository
**File: `src/4_infrastructure/database/repositories/test_repository.py`**

**Operations:**
- `create()`: Save generated test
- `get_by_id()`: Retrieve test by ID
- `get_by_lecture()`: Get all tests for a lecture

### 4. Domain Entities
**File: `src/3_domain/entities/test.py`**

**Test Entity:**
```python
@dataclass
class Test:
    id: str
    lecture_id: str
    title: str
    difficulty: str
    total_points: int
    time_limit: int  # minutes
    questions: List[Dict]
    created_at: Optional[datetime]
```

**Question Structure:**
```python
{
    "question_id": "q1",
    "type": "mcq",
    "question_text": "What is...?",
    "options": ["A", "B", "C", "D"],
    "correct_answer": "A",
    "points": 2,
    "difficulty": "medium",
    "bloom_level": "apply",
    "explanation": "According to the lecture..."
}
```

### 5. API Endpoints
**File: `src/1_presentation/api/v1/endpoints/tests.py`**

#### Generate Test
```http
POST /api/v1/tests/generate?course_id={course_id}
Authorization: Bearer <token>
Content-Type: application/json

{
    "week_number": 1,
    "difficulty": "medium",
    "question_types": ["mcq", "true_false"],
    "question_count": 10
}

Response (201):
{
    "id": "test_abc123",
    "lecture_id": "lec_xyz789",
    "title": "Week 1 Test - Medium",
    "difficulty": "medium",
    "total_points": 15,
    "time_limit": 30,
    "questions": [...],
    "created_at": "2026-03-05T22:00:00Z"
}
```

#### Get Test
```http
GET /api/v1/tests/{test_id}
Authorization: Bearer <token>

Response (200):
{
    "id": "test_abc123",
    "lecture_id": "lec_xyz789",
    "title": "Week 1 Test - Medium",
    ...
}
```

#### Get Lecture Tests
```http
GET /api/v1/tests/lecture/{lecture_id}
Authorization: Bearer <token>

Response (200):
{
    "total": 2,
    "tests": [...]
}
```

### 6. Pydantic Schemas
**File: `src/1_presentation/schemas/test.py`**

- `TestGenerateRequest`: Request validation
- `QuestionResponse`: Question data
- `TestResponse`: Test data
- `TestListResponse`: List of tests

## RAG Integration

### Context Retrieval Flow
```
1. User requests test generation
   ↓
2. Query: "lecture content, key concepts, examples"
   ↓
3. Generate query embedding (OpenAI)
   ↓
4. Search pgvector (cosine similarity)
   ↓
5. Retrieve top 5 relevant chunks
   ↓
6. Format context for LLM
   ↓
7. Generate questions with context
   ↓
8. Validate and save
```

### Context Retriever
**File: `src/3_domain/memory/context_retriever.py`**

**Method: `retrieve_for_test_generation()`**
- Retrieves relevant lecture chunks
- Formats context for LLM consumption
- Returns structured context string

## LLM Prompt Engineering

### System Prompt
```
You are an expert educational assessment designer.
Generate high-quality test questions based on provided lecture material.

Difficulty Level: MEDIUM
Bloom's Taxonomy Level: Apply and Analyze

CRITICAL REQUIREMENTS:
1. Questions MUST be based ONLY on the provided context
2. Answers MUST be factually correct
3. For MCQ: Create plausible distractors
4. Output ONLY valid JSON
```

### User Prompt
```
Based on the following lecture material, generate 10 test questions.

LECTURE MATERIAL:
[RAG context chunks]

REQUIREMENTS:
- Question types: mcq, true_false
- Difficulty: medium
- Total questions: 10
- Distribute points appropriately
```

## Quality Validation

### Validation Rules
1. **Question text**: Minimum 10 characters
2. **MCQ options**: At least 2 options
3. **Correct answer**: Must be in options list
4. **Points**: Minimum 1 point
5. **JSON format**: Valid JSON structure

### Filtering
- Invalid questions are filtered out
- Only validated questions are saved
- Ensures high-quality output

## Testing

### Test Script
**File: `scripts/test_generation.py`**

**Workflow:**
1. Login
2. Get courses
3. Find completed lecture
4. Generate test
5. Display questions

**Run:**
```bash
python scripts/test_generation.py
```

### Manual Testing
```bash
# 1. Upload and process lecture (Phases 5-7)
curl -X POST http://localhost:8000/api/v1/lectures/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "course_id=course_abc" \
  -F "week_number=1" \
  -F "title=Intro to AI" \
  -F "file=@lecture.pdf"

# 2. Wait for processing (check status)
curl -X GET http://localhost:8000/api/v1/lectures/lec_abc/status \
  -H "Authorization: Bearer TOKEN"

# 3. Generate test
curl -X POST "http://localhost:8000/api/v1/tests/generate?course_id=course_abc" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "week_number": 1,
    "difficulty": "medium",
    "question_types": ["mcq", "true_false"],
    "question_count": 10
  }'
```

## Architecture Highlights

### Clean Architecture
- **Domain Layer**: Test generator agent, entities
- **Application Layer**: Generate test use case
- **Infrastructure Layer**: Test repository, LLM integration
- **Presentation Layer**: API endpoints, schemas

### Design Patterns
- **Agent Pattern**: Encapsulated test generation logic
- **Repository Pattern**: Data access abstraction
- **Strategy Pattern**: Different question types
- **Factory Pattern**: LLM adapter creation

### Key Features
- **RAG-Powered**: Uses lecture embeddings for context
- **Bloom's Taxonomy**: Aligned with educational standards
- **Quality Validation**: Ensures high-quality questions
- **Flexible**: Configurable difficulty and question types
- **Type-Safe**: Full type hints throughout

## Example Output

### Generated Test
```json
{
  "id": "test_abc123",
  "title": "Week 1 Test - Medium",
  "difficulty": "medium",
  "total_points": 15,
  "time_limit": 30,
  "questions": [
    {
      "question_id": "q1",
      "type": "mcq",
      "question_text": "What is the primary purpose of gradient descent in machine learning?",
      "options": [
        "To minimize the loss function",
        "To maximize accuracy",
        "To normalize data",
        "To split training data"
      ],
      "correct_answer": "To minimize the loss function",
      "points": 2,
      "difficulty": "medium",
      "bloom_level": "understand",
      "explanation": "According to the lecture, gradient descent is an optimization algorithm used to minimize the loss function by iteratively adjusting model parameters."
    },
    {
      "question_id": "q2",
      "type": "true_false",
      "question_text": "Neural networks can only be used for classification tasks.",
      "options": ["True", "False"],
      "correct_answer": "False",
      "points": 1,
      "difficulty": "easy",
      "bloom_level": "remember",
      "explanation": "Neural networks can be used for both classification and regression tasks, as mentioned in the lecture."
    }
  ]
}
```

## Performance Considerations

### Optimization
- **Caching**: Context retrieval results can be cached
- **Batch Processing**: Generate multiple tests in parallel
- **Token Limits**: Context limited to avoid token overflow
- **Async Operations**: All database and LLM calls are async

### Scalability
- **Horizontal**: Add more API servers
- **Vertical**: Increase LLM rate limits
- **Database**: pgvector handles large embedding datasets
- **Caching**: Redis for frequently accessed tests

## Error Handling

### Common Errors
1. **Lecture not found**: 404 Not Found
2. **Lecture not processed**: 400 Bad Request
3. **Unauthorized access**: 403 Forbidden
4. **LLM API error**: Retries with exponential backoff
5. **Invalid JSON**: Validation error with details

### Graceful Degradation
- Invalid questions filtered out
- Minimum question count enforced
- Fallback to default values

## Files Created/Modified

### Created (5 files)
1. `src/3_domain/agents/test_generator_agent.py`
2. `src/4_infrastructure/database/repositories/test_repository.py`
3. `src/2_application/usecases/test/generate_test.py`
4. `src/1_presentation/api/v1/endpoints/tests.py`
5. `scripts/test_generation.py`
6. `PHASE8_COMPLETE.md`

### Modified (3 files)
1. `src/3_domain/entities/test.py` - Updated entity structure
2. `src/1_presentation/schemas/test.py` - Updated schemas
3. `src/1_presentation/api/v1/router.py` - Added tests router

## Next Steps (Phase 9 - Optional)

### Evaluation Agent
- Submit test answers
- Auto-grade MCQ and True/False
- AI-powered essay grading
- Detailed feedback generation
- Score calculation

### Student Attempts
- Track test submissions
- Store answers and scores
- Attempt history
- Performance analytics

## Status: ✅ COMPLETE
Phase 8 implementation is complete. Test generation with RAG is fully functional and ready for use.
