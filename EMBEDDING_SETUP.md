# Embedding Тохиргоо

## Embedding гэж юу вэ?

Embedding нь текстийг тоон вектор болгон хөрвүүлэх процесс. Энэ нь RAG (Retrieval Augmented Generation)-д ашиглагддаг:

1. **Хичээл боловсруулах үед**: Текстийг chunk-уудад хуваагаад embedding үүсгэж database-д хадгална
2. **Тест үүсгэх үед**: Query-г embedding болгоод хамгийн ойр chunk-уудыг олж авна (semantic search)
3. **Context өгөх**: Олдсон chunk-уудыг Claude-д өгч асуулт үүсгүүлнэ

## Одоогийн тохиргоо

### Provider-үүд:
- **Test generation (Claude)**: Асуулт үүсгэх
- **Embeddings (Mock)**: Semantic search (OpenAI quota шаардлагагүй)

### Яагаад Mock ашигладаг вэ?

1. **OpenAI quota дууссан** - Таны OpenAI API key-ийн лимит дууссан
2. **Claude embedding үгүй** - Claude нь embedding API өгдөггүй
3. **Development-д хангалттай** - Mock embedding нь тест хийхэд хангалттай

## Mock Embedding

Mock embedding нь:
- Текстийн hash-аас тогтвортой 1536-dimensional vector үүсгэнэ
- Ижил текст үргэлж ижил embedding өгнө
- Semantic meaning-г ойлгодоггүй (бодит embedding шиг биш)
- Гэхдээ RAG workflow-г тест хийхэд хангалттай

### Давуу тал:
✅ API key шаардлагагүй  
✅ Quota limit байхгүй  
✅ Хурдан  
✅ Үнэгүй  
✅ Development-д тохиромжтой  

### Сул тал:
❌ Semantic similarity тооцоолдоггүй  
❌ Холбогдолтой context олдоггүй  
❌ Production-д тохиромжгүй  

## Production тохиргоо

Production-д бодит embedding хэрэгтэй бол:

### Сонголт 1: OpenAI Embeddings

```bash
# .env файл
DEFAULT_LLM_PROVIDER=claude  # Test generation-д Claude
OPENAI_API_KEY=sk-...  # Quota-тай API key

# llm_factory.py-д өөрчлөлт хийх:
# create_embedding_adapter() функцийг OpenAI буцаах болгох
```

**Зардал:**
- text-embedding-3-small: $0.02 / 1M tokens
- text-embedding-3-large: $0.13 / 1M tokens

**Давуу тал:**
- Маш сайн чанартай semantic search
- Олон хэлийг дэмждэг
- Хурдан

### Сонголт 2: Sentence Transformers (Local)

```bash
# requirements.txt-д нэмэх
sentence-transformers==2.2.2

# Шинэ adapter үүсгэх
# src/infrastructure/external/llm/sentence_transformer_adapter.py
```

**Давуу тал:**
- Үнэгүй (local)
- API key шаардлагагүй
- Privacy (өгөгдөл гадагш явахгүй)

**Сул тал:**
- Удаан (CPU дээр)
- Санах ой их зарцуулна
- OpenAI-аас чанар муу

### Сонголт 3: Hybrid (Claude + OpenAI Embeddings)

```bash
# .env файл
DEFAULT_LLM_PROVIDER=claude  # Test generation
EMBEDDING_PROVIDER=openai    # Embeddings
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Энэ нь хамгийн сайн сонголт:
- Claude: Чанартай асуулт үүсгэнэ
- OpenAI: Сайн чанартай semantic search

## Одоогийн код

### LLM Factory

```python
@staticmethod
def create_embedding_adapter() -> ILLMAdapter:
    """
    Create adapter for embeddings.
    
    Note: Claude doesn't support embeddings, so we use mock for development.
    For production with real embeddings, use OpenAI.
    """
    provider = getattr(settings, "DEFAULT_LLM_PROVIDER", "openai").lower()
    
    # Always use mock for embeddings in development
    # This avoids OpenAI API quota issues
    if provider in ["mock", "claude"]:
        return MockLLMAdapter()
    
    # Only use OpenAI if explicitly set and you have quota
    return OpenAIAdapter()
```

### Хэрэглээ

```python
# Test generation
llm_adapter = LLMFactory.create_default_adapter()  # Claude
test_generator = TestGeneratorAgent(llm_adapter, ...)

# Embeddings
embedding_adapter = LLMFactory.create_embedding_adapter()  # Mock
embedding_service = EmbeddingService(embedding_adapter)
```

## Тест хийх

### 1. Mock embedding ажиллаж байгаа эсэхийг шалгах

```python
# Python shell
from src.infrastructure.external.llm.mock_adapter import MockLLMAdapter

adapter = MockLLMAdapter()
embedding = await adapter.embed("Hello world")

print(f"Embedding dimension: {len(embedding)}")  # 1536
print(f"First 5 values: {embedding[:5]}")
```

### 2. Хичээл боловсруулах

```bash
# Lecture upload хийх
# Backend logs-д харах:
[MemoryManager] Storing lecture memory...
[EmbeddingService] Generating embeddings for 10 chunks...
[EmbeddingRepository] Created 10 embeddings
```

### 3. Тест үүсгэх

```bash
# Test generation хийх
# Backend logs-д харах:
[TestGenerator] Retrieved context length: 2500
[TestGenerator] Context chunks: 5
```

## Алдаа засах

### "OpenAI embedding error: insufficient_quota"

```bash
# Backend дахин эхлүүлэх (mock ашиглах болно)
uvicorn src.main:app --reload

# Шалгах
curl http://127.0.0.1:8000/health
```

### "No embeddings found"

```bash
# Database шалгах
psql -U postgres -d study_assistant -c "
  SELECT lecture_id, COUNT(*) as embedding_count
  FROM embeddings
  GROUP BY lecture_id;
"

# Хэрэв хоосон бол хичээл дахин боловсруулах
```

### "Context retrieval failed"

```bash
# Memory manager logs шалгах
# Mock embedding нь semantic search хийдэггүй
# Гэхдээ random chunks буцаана
```

## Дүгнэлт

**Development (одоо):**
- Test generation: Claude ✅
- Embeddings: Mock ✅
- Зардал: Зөвхөн Claude API (~$0.03/test)

**Production (ирээдүйд):**
- Test generation: Claude
- Embeddings: OpenAI эсвэл Sentence Transformers
- Зардал: Claude + OpenAI (~$0.05/test)

Mock embedding нь development-д хангалттай, production-д OpenAI embeddings ашиглах!
