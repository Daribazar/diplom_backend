# Database Layer Guide

## Overview

The database layer follows Clean Architecture principles with clear separation between domain logic and infrastructure concerns.

## Architecture

```
Domain Layer (3_domain/)
    ↓ (uses interfaces)
Infrastructure Layer (4_infrastructure/)
    ↓ (implements)
Database (PostgreSQL)
```

## Key Concepts

### 1. Domain Entities (Pure Business Logic)

Located in `src/3_domain/entities/`

**Example: Lecture Entity**
```python
from src.3_domain.entities.lecture import Lecture

# Create domain entity
lecture = Lecture(
    id="lec_abc123",
    course_id="course_xyz789",
    week_number=1,
    title="Introduction to ML",
    status="pending"
)

# Business logic methods
lecture.mark_as_processing()  # State transition
lecture.mark_as_completed(content, concepts, embeddings)
lecture.is_ready_for_test_generation()  # Business query
```

### 2. Database Models (Infrastructure)

Located in `src/4_infrastructure/database/models/`

**Example: LectureModel**
```python
from src.4_infrastructure.database.models.lecture import LectureModel

# SQLAlchemy model - handles persistence
db_lecture = LectureModel(
    id="lec_abc123",
    course_id="course_xyz789",
    week_number=1,
    title="Introduction to ML",
    status="pending",
    key_concepts=["ML", "AI"],  # JSONB
    embedding_ids=["emb_1"]     # JSONB
)
```

### 3. Repositories (Bridge Pattern)

Located in `src/4_infrastructure/database/repositories/`

**Example: LectureRepository**
```python
from src.4_infrastructure.database.repositories.lecture_repository import LectureRepository

async def create_lecture(db: AsyncSession):
    # Create domain entity
    lecture = Lecture(
        id="lec_new123",
        course_id="course_xyz789",
        week_number=2,
        title="Linear Regression"
    )
    
    # Use repository to persist
    repo = LectureRepository(db)
    saved_lecture = await repo.create(lecture)
    
    return saved_lecture
```

## Usage Patterns

### Pattern 1: Create Entity

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db
from src.3_domain.entities.course import Course
from src.4_infrastructure.database.repositories.course_repository import CourseRepository

@app.post("/courses")
async def create_course(
    name: str,
    code: str,
    semester: str,
    db: AsyncSession = Depends(get_db)
):
    # 1. Create domain entity
    course = Course(
        id=f"course_{uuid.uuid4().hex[:12]}",
        name=name,
        code=code,
        semester=semester,
        owner_id="user_123"
    )
    
    # 2. Use repository to save
    repo = CourseRepository(db)
    saved_course = await repo.create(course)
    
    return saved_course
```

### Pattern 2: Query and Update

```python
@app.put("/lectures/{lecture_id}/complete")
async def complete_lecture(
    lecture_id: str,
    content: str,
    concepts: list[str],
    db: AsyncSession = Depends(get_db)
):
    # 1. Get entity from repository
    repo = LectureRepository(db)
    lecture = await repo.get_by_id(lecture_id)
    
    if not lecture:
        raise HTTPException(404, "Lecture not found")
    
    # 2. Apply business logic
    lecture.mark_as_completed(
        content=content,
        key_concepts=concepts,
        embedding_ids=["emb_1", "emb_2"]
    )
    
    # 3. Save changes
    updated_lecture = await repo.update(lecture)
    
    return updated_lecture
```

### Pattern 3: List with Filtering

```python
@app.get("/courses/{course_id}/lectures")
async def get_lectures(
    course_id: str,
    db: AsyncSession = Depends(get_db)
):
    repo = LectureRepository(db)
    lectures = await repo.get_by_course(course_id)
    
    # Filter using business logic
    ready_for_tests = [
        lec for lec in lectures 
        if lec.is_ready_for_test_generation()
    ]
    
    return ready_for_tests
```

## Database Session Management

### Using Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db

@app.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)  # Auto-managed session
):
    # Session is automatically:
    # - Created before request
    # - Committed after successful response
    # - Rolled back on error
    # - Closed after request
    
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    return user
```

### Manual Session Management

```python
from src.4_infrastructure.database.connection import async_session_maker

async def background_task():
    async with async_session_maker() as session:
        try:
            repo = UserRepository(session)
            user = await repo.get_by_id("user_123")
            
            # Do work...
            
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## JSONB Columns

### Storing Flexible Data

```python
# Lecture model has JSONB columns
lecture = Lecture(
    id="lec_123",
    course_id="course_456",
    week_number=1,
    title="Introduction",
    key_concepts=["ML", "AI", "Data"],      # List stored as JSONB
    embedding_ids=["emb_1", "emb_2"],       # List stored as JSONB
)

# Test model stores questions as JSONB
test = TestModel(
    id="test_123",
    lecture_id="lec_123",
    questions=[
        {
            "id": 1,
            "text": "What is ML?",
            "type": "multiple_choice",
            "options": ["A", "B", "C", "D"],
            "correct": "A"
        },
        {
            "id": 2,
            "text": "Explain AI",
            "type": "short_answer",
            "correct": "..."
        }
    ]
)
```

### Querying JSONB

```python
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB

# Query lectures with specific concept
result = await session.execute(
    select(LectureModel)
    .where(LectureModel.key_concepts.contains(["ML"]))
)
```

## Migrations with Alembic

### Create Migration

```bash
# Auto-generate from model changes
poetry run alembic revision --autogenerate -m "Add new column"

# Manual migration
poetry run alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
poetry run alembic upgrade head

# Upgrade one version
poetry run alembic upgrade +1

# Downgrade one version
poetry run alembic downgrade -1

# Show current version
poetry run alembic current

# Show history
poetry run alembic history
```

### Migration File Example

```python
"""Add metadata column to lectures

Revision ID: abc123
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    op.add_column('lectures',
        sa.Column('metadata', postgresql.JSONB, default=dict)
    )

def downgrade() -> None:
    op.drop_column('lectures', 'metadata')
```

## Testing

### Unit Tests (Domain Logic)

```python
def test_lecture_state_transitions():
    lecture = Lecture(
        id="lec_test",
        course_id="course_test",
        week_number=1,
        title="Test"
    )
    
    # Test state transition
    lecture.mark_as_processing()
    assert lecture.status == "processing"
    
    # Test validation
    with pytest.raises(ValueError):
        lecture.mark_as_completed("short", [], [])  # Too short
```

### Integration Tests (Database)

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_lecture(db_session: AsyncSession):
    lecture = Lecture(
        id="lec_test",
        course_id="course_test",
        week_number=1,
        title="Test Lecture"
    )
    
    repo = LectureRepository(db_session)
    saved = await repo.create(lecture)
    
    assert saved.id == lecture.id
    assert saved.title == lecture.title
```

## Best Practices

### 1. Always Use Domain Entities in Business Logic

❌ **Bad:**
```python
# Don't manipulate database models directly
db_lecture = await session.get(LectureModel, lecture_id)
db_lecture.status = "completed"  # No validation!
```

✅ **Good:**
```python
# Use domain entities with business logic
lecture = await repo.get_by_id(lecture_id)
lecture.mark_as_completed(content, concepts, embeddings)  # Validated!
await repo.update(lecture)
```

### 2. Keep Repositories Simple

❌ **Bad:**
```python
class LectureRepository:
    async def create_and_process_lecture(self, lecture, file):
        # Too much logic in repository!
        saved = await self.create(lecture)
        content = extract_text(file)
        concepts = analyze_content(content)
        # ...
```

✅ **Good:**
```python
class LectureRepository:
    async def create(self, lecture: Lecture) -> Lecture:
        # Simple CRUD only
        db_lecture = LectureModel(...)
        self.session.add(db_lecture)
        await self.session.flush()
        return self._to_entity(db_lecture)
```

### 3. Use Type Hints

```python
async def get_by_id(self, lecture_id: str) -> Optional[Lecture]:
    """Find lecture by ID."""
    result = await self.session.execute(
        select(LectureModel).where(LectureModel.id == lecture_id)
    )
    db_lecture = result.scalar_one_or_none()
    if not db_lecture:
        return None
    return self._to_entity(db_lecture)
```

### 4. Handle Errors Gracefully

```python
from src.core.exceptions import NotFoundException

async def get_lecture_or_404(lecture_id: str, db: AsyncSession) -> Lecture:
    repo = LectureRepository(db)
    lecture = await repo.get_by_id(lecture_id)
    
    if not lecture:
        raise NotFoundException(f"Lecture {lecture_id} not found")
    
    return lecture
```

## Common Queries

### Get User's Courses

```python
repo = CourseRepository(db)
courses = await repo.get_by_owner(user_id)
```

### Get Course Lectures

```python
repo = LectureRepository(db)
lectures = await repo.get_by_course(course_id)
```

### Get Processed Lectures

```python
lectures = await repo.get_by_course(course_id)
processed = [lec for lec in lectures if lec.is_processed()]
```

## Troubleshooting

### Connection Issues

```bash
# Test connection
poetry run python scripts/test_db_connection.py

# Check PostgreSQL is running
brew services list | grep postgresql
```

### Migration Issues

```bash
# Reset database (CAUTION: deletes all data)
poetry run python scripts/init_db.py

# Check migration status
poetry run alembic current
poetry run alembic history
```

### Import Errors

```python
# Always import from correct layer
from src.3_domain.entities.lecture import Lecture  # Domain
from src.4_infrastructure.database.models.lecture import LectureModel  # Infrastructure
from src.4_infrastructure.database.repositories.lecture_repository import LectureRepository
```

## Summary

- **Domain entities** = Business logic (no database concerns)
- **Database models** = SQLAlchemy models (persistence)
- **Repositories** = Bridge between domain and database
- **JSONB** = Flexible data storage
- **Async/await** = All database operations
- **Type hints** = All functions
- **Alembic** = Database migrations
