# Claude ашиглан Тест Үүсгэх

## Тохиргоо

Claude-ийг ашиглахын тулд `.env` файлд дараах өөрчлөлтүүдийг хийсэн:

### 1. LLM Provider солих
```bash
# .env файл
DEFAULT_LLM_PROVIDER=claude  # mock-оос claude болгосон
```

### 2. API Key шалгах
```bash
# .env файл
ANTHROPIC_API_KEY=sk-ant-api03-...  # Таны Claude API key
```

### 3. Embedding тохиргоо
**Анхаар:** Claude нь embedding дэмждэггүй. Embedding-д mock ашигладаг (OpenAI API quota шаардлагагүй).

Хэрэв production-д бодит embedding хэрэгтэй бол:
- OpenAI API key-тэй байх
- `.env` файлд `DEFAULT_LLM_PROVIDER=openai` эсвэл
- Embedding-ийн тусгай provider нэмэх

Одоогийн тохиргоо:
- **Test generation**: Claude (чанартай асуулт)
- **Embeddings**: Mock (OpenAI quota шаардлагагүй)

## Claude-ийн давуу тал

✅ **Чанартай асуулт** - Claude нь илүү сайн чанартай, утга учиртай асуулт үүсгэнэ  
✅ **Монгол хэл** - System prompt-д монгол хэл дээр асуулт үүсгэхийг тодорхой заасан  
✅ **Контекст ойлголт** - Хичээлийн материалыг сайн ойлгож, холбогдолтой асуулт үүсгэнэ  
✅ **Bloom's Taxonomy** - Хүндрэлийн түвшинд тохирсон асуулт үүсгэнэ  
✅ **Тайлбар** - Асуулт бүрт дэлгэрэнгүй тайлбар өгнө  

## System Prompt Өөрчлөлтүүд

### Үндсэн шаардлагууд:
1. **Монгол хэл** - Бүх асуулт монгол хэл дээр байх
2. **Материалд үндэслэсэн** - Зөвхөн өгөгдсөн хичээлийн материалаас асуулт үүсгэх
3. **Зөв хариулт** - Бүх хариулт материалд нийцсэн байх
4. **Чанартай сонголтууд** - MCQ-д бодитой боловч буруу сонголтууд үүсгэх

### Асуултын чанарын стандарт:
- **MCQ**: 4 сонголт, бодитой диstractors
- **Үнэн/Худал**: Тодорхой, ойлгомжтой мэдэгдэл
- **Эссэ**: Тодорхой үнэлгээний шалгуур
- **Грамматик**: Монгол хэлний дүрэм зөв
- **Терминологи**: Техникийн нэр томъёо зөв

## Ашиглах заавар

### 1. Backend эхлүүлэх
```bash
cd study-assistant-backend
source venv/bin/activate

# FastAPI
uvicorn src.main:app --reload --port 8000

# Celery (өөр terminal)
celery -A src.infrastructure.queue.celery_app worker --loglevel=info
```

### 2. Хичээл оруулах
- Frontend: http://localhost:3000/courses/[courseId]/lectures/upload
- PDF файл оруулах
- Status "completed" болтол хүлээх

### 3. Тест үүсгэх
- Frontend: http://localhost:3000/courses/[courseId]/tests/generate
- Форм бөглөх:
  - Долоо хоног: 1
  - MCQ тоо: 5
  - Үнэн/Худал тоо: 3
  - Хүндрэл: medium
- "Тест үүсгэх" дарах

### 4. Backend logs шалгах
```
[GenerateTestUseCase] Generating test for lecture lec_xxx
[TestGenerator] Retrieved context length: 2500
[TestGenerator] Parsing LLM response (first 200 chars): {"questions": [{"question_id": "q1"...
[TestGenerator] Parsed 8 questions from LLM response
[TestGenerator] Successfully created 8 Question objects
[TestRepository] Creating test test_xxx
[TestRepository] Questions count: 8
[TestRepository] Test saved. DB questions count: 8
```

### 5. Тест өгөх
- Frontend: http://localhost:3000/courses/[courseId]/tests/[testId]/take
- Асуултууд монгол хэл дээр харагдана
- Чанартай, утга учиртай асуултууд

## Жишээ асуултууд

Claude үүсгэх асуултын жишээ:

### MCQ (Easy - Remember):
```
Асуулт: Нейрон сүлжээний үндсэн бүрэлдэхүүн хэсгүүд юу вэ?

Сонголтууд:
А) Зөвхөн нейронууд
Б) Нейрон, холболт, жин
В) Зөвхөн холболтууд
Г) Өгөгдлийн сан

Зөв хариулт: Б) Нейрон, холболт, жин

Тайлбар: Нейрон сүлжээ нь гурван үндсэн бүрэлдэхүүн хэсгээс бүрдэнэ: 
нейронууд (nodes), холболтууд (connections), жингүүд (weights). 
Эдгээр нь хамтдаа ажиллаж өгөгдлийг боловсруулдаг.
```

### MCQ (Medium - Apply):
```
Асуулт: Activation function-ий үүрэг юу вэ?

Сонголтууд:
А) Өгөгдлийг хадгалах
Б) Нейроны гаралтыг тооцоолж, шугаман бус байдал нэмэх
В) Сүлжээг сургах
Г) Алдааг тооцоолох

Зөв хариулт: Б) Нейроны гаралтыг тооцоолж, шугаман бус байдал нэмэх

Тайлбар: Activation function нь нейроны оролтыг боловсруулж гаралт 
үүсгэдэг бөгөөд сүлжээнд шугаман бус байдал (non-linearity) нэмдэг. 
Энэ нь сүлжээг илүү төвөгтэй функцүүдийг суралцах боломжтой болгодог.
```

### True/False (Easy - Remember):
```
Асуулт: Нейрон сүлжээ өгөгдлөөс суралцах чадвартай.

Хариулт: Үнэн

Тайлбар: Нейрон сүлжээ сургалтын өгөгдлийг ашиглан жингээ 
тохируулж, алдаагаа багасгаж, гүйцэтгэлээ сайжруулдаг. 
Энэ нь машин суралцлын үндсэн зарчим юм.
```

### MCQ (Hard - Analyze):
```
Асуулт: Backpropagation алгоритмын үндсэн алхамууд ямар дарааллаар явагддаг вэ?

Сонголтууд:
А) Gradient тооцоолох → Forward pass → Жин шинэчлэх → Алдаа тооцоолох
Б) Forward pass → Алдаа тооцоолох → Gradient тооцоолох → Жин шинэчлэх
В) Жин шинэчлэх → Forward pass → Алдаа тооцоолох → Gradient тооцоолох
Г) Алдаа тооцоолох → Forward pass → Gradient тооцоолох → Жин шинэчлэх

Зөв хариулт: Б) Forward pass → Алдаа тооцоолох → Gradient тооцоолох → Жин шинэчлэх

Тайлбар: Backpropagation нь дараах дарааллаар ажилладаг:
1. Forward pass - оролтыг дамжуулж таамаглал гаргах
2. Алдаа тооцоолох - таамаглал болон бодит утгын зөрүүг олох
3. Gradient тооцоолох - алдааг буцааж дамжуулж gradient олох
4. Жин шинэчлэх - gradient ашиглан жингүүдийг сайжруулах
```

## Mock vs Claude харьцуулалт

| Шинж чанар | Mock | Claude |
|-----------|------|--------|
| Асуултын чанар | Урьдчилан бэлтгэсэн | AI үүсгэсэн, чанартай |
| Материалд үндэслэсэн | Үгүй | Тийм |
| Монгол хэл | Тийм (хатуу кодлосон) | Тийм (AI үүсгэсэн) |
| Олон янз байдал | Үргэлж ижил | Өөр өөр |
| Хүндрэл | Тогтмол | Тохируулж болно |
| Тайлбар | Энгийн | Дэлгэрэнгүй |
| API зардал | Үнэгүй | Төлбөртэй |

## API зардал

Claude API-ийн үнэ (Claude Sonnet 4):
- Input: ~$3 / 1M tokens
- Output: ~$15 / 1M tokens

Тест үүсгэх (8 асуулт):
- Input: ~2000 tokens (хичээлийн материал + prompt)
- Output: ~1500 tokens (асуултууд)
- Зардал: ~$0.03 тест бүрт

## Алдаа засах

### 1. "Claude API error: Invalid API key"
```bash
# .env файлд API key шалгах
cat .env | grep ANTHROPIC_API_KEY

# Шинэ API key авах: https://console.anthropic.com/
```

### 2. "OpenAI embedding error: insufficient_quota"
```bash
# Энэ алдаа гарвал embedding-д mock ашиглах тохиргоо хийгдсэн эсэхийг шалгах
# llm_factory.py файлд create_embedding_adapter() функц:
# - claude provider бол mock ашиглах ёстой
# - Backend дахин эхлүүлэх хэрэгтэй

# Backend дахин эхлүүлэх
uvicorn src.main:app --reload
```

### 3. "No lecture content found"
```bash
# Хичээл боловсруулагдсан эсэхийг шалгах
psql -U postgres -d study_assistant -c "
  SELECT id, title, status, content_length 
  FROM lectures 
  WHERE status = 'completed' 
  ORDER BY created_at DESC 
  LIMIT 5;
"
```

### 4. "Failed to parse LLM response as JSON"
```bash
# Backend logs-д LLM response харах
# Claude заримдаа markdown code block буцаадаг:
# ```json
# {...}
# ```
# Код аль хэдийн энийг цэвэрлэдэг
```

### 5. Асуултууд англи хэл дээр байвал
```bash
# System prompt шалгах
# "Generate questions in MONGOLIAN language" гэсэн байх ёстой
```

## Сайжруулалт

Хэрэв асуултын чанар хангалтгүй бол:

1. **Temperature бууруулах** (0.7 → 0.5) - илүү тогтвортой
2. **System prompt сайжруулах** - илүү дэлгэрэнгүй заавар
3. **Context нэмэх** - илүү их хичээлийн материал
4. **Few-shot examples** - жишээ асуулт нэмэх

## Дүгнэлт

✅ Claude ашиглах нь илүү сайн чанартай тест үүсгэнэ  
✅ Монгол хэл дээр зөв асуулт үүсгэнэ  
✅ Хичээлийн материалд үндэслэсэн байна  
✅ Bloom's Taxonomy-д нийцсэн байна  
✅ Дэлгэрэнгүй тайлбартай байна  

Mock нь зөвхөн тест хийхэд ашиглах, production-д Claude ашиглах!
