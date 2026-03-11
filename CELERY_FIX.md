# Celery Worker Алдаа Засах

## Асуудал
`UnmappedInstanceError: Class 'src.domain.entities.lecture.Lecture' is not mapped`

Энэ алдаа нь:
1. Celery worker SQLAlchemy model-уудыг зөв import хийдэггүй байсан
2. Domain entity (Lecture) болон Database model (LectureModel)-ийг андуурч байсан
3. `session.refresh()` domain entity дээр ажиллахгүй

## Засварууд

### 1. `celery_app.py` - Model-уудыг import хийх
```python
# Import all SQLAlchemy models to ensure they're registered
from src.infrastructure.database.models.user import UserModel
from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.lecture import LectureModel
from src.infrastructure.database.models.test import TestModel, QuestionModel
from src.infrastructure.database.models.evaluation import EvaluationModel, AnswerModel
from src.infrastructure.database.models.embedding import LectureEmbedding
```

### 2. `lecture_processing.py` - session.refresh() устгах
```python
# Буруу:
await session.refresh(db_lecture)  # db_lecture нь domain entity

# Зөв:
db_lecture_updated = await lecture_repo.get_by_id(lecture_id)
```

## Celery Worker дахин эхлүүлэх

```bash
# Одоо ажиллаж байгаа worker-ийг зогсоох
# Ctrl+C дарах эсвэл:
pkill -f "celery worker"

# Дахин эхлүүлэх
cd study-assistant-backend
source venv/bin/activate
celery -A src.infrastructure.queue.celery_app worker --loglevel=info
```

## Шалгах

1. Lecture upload хийх
2. Celery worker log-ийг харах:
   - "Starting lecture processing: lec_xxx"
   - "Lecture processing completed: lec_xxx"
   - "Final status: completed"

3. Lecture status шалгах:
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/lectures/lec_xxx/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Анхаарах зүйлс

- Celery worker эхлэхдээ бүх SQLAlchemy model-уудыг import хийх ёстой
- Domain entity болон Database model-ийг андуурахгүй байх
- `session.refresh()` зөвхөн SQLAlchemy model дээр ажиллана
- Repository-г ашиглаж дахин query хийх нь илүү найдвартай
