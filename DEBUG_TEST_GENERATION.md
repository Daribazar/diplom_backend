# Test Generation Debug Guide

## Асуудал
Tests үүсч байгаа боловч questions хоосон (question_count = 0)

## Шалгах зүйлс

### 1. Backend logs шалгах
Test generation request ирэхэд:
```bash
# Backend terminal дээр харах
# Ямар алдаа гарч байгааг харах
```

### 2. Lecture content шалгах
```sql
-- PostgreSQL дээр
SELECT id, title, status, 
       length(content) as content_length,
       array_length(key_concepts, 1) as concepts_count
FROM lectures 
WHERE status = 'completed'
ORDER BY created_at DESC 
LIMIT 5;
```

### 3. Embeddings шалгах
```sql
SELECT lecture_id, count(*) as chunk_count
FROM lecture_embeddings
GROUP BY lecture_id;
```

### 4. Test generation manually шалгах
```bash
# Python shell
python
>>> from src.infrastructure.database.connection import async_session_maker
>>> from src.infrastructure.database.repositories.lecture_repository import LectureRepository
>>> import asyncio
>>> 
>>> async def check():
...     async with async_session_maker() as session:
...         repo = LectureRepository(session)
...         lecture = await repo.get_by_id("lec_xxx")  # Replace with actual ID
...         print(f"Status: {lecture.status}")
...         print(f"Content length: {len(lecture.content)}")
...         print(f"Key concepts: {lecture.key_concepts}")
>>> 
>>> asyncio.run(check())
```

## Магадгүй шалтгаанууд

1. **AI Agent алдаа** - OpenAI/Claude API key буруу эсвэл quota дууссан
2. **Lecture content хоосон** - PDF текст задлагдаагүй
3. **Embeddings байхгүй** - RAG context олдохгүй байна
4. **Exception catch хийгдсэн** - Алдаа log-д харагдахгүй байна

## Шийдэл

### Түр зуур: Mock questions ашиглах
Test generation usecase-д fallback нэмэх:

```python
# generate_test.py дээр
if not result.questions or len(result.questions) == 0:
    # Fallback to mock questions
    from src.domain.entities.test import Question
    result.questions = [
        Question(
            question_id=f"q{i}",
            type=QuestionType.MCQ,
            question_text=f"Sample question {i}",
            options=["A", "B", "C", "D"],
            correct_answer="A",
            points=2,
            difficulty=difficulty_enum,
            bloom_level="Remember",
            explanation="Sample explanation"
        )
        for i in range(1, min(question_count + 1, 6))
    ]
```

## Backend logs харах
Test үүсгэх үед backend terminal дээр:
- "Generating test..." гэсэн мэдээлэл
- AI agent response
- Questions count
- Алдааны мэдээлэл

Эдгээрийг харуулаарай!
