# Phase 2 Complete: Database Setup

## ✅ What Was Implemented

### 1. Database Models (SQLAlchemy 2.0 Async)

All models use:
- String-based UUIDs for primary keys (e.g., `user_abc123`, `course_xyz789`)
- JSONB columns for flexible data storage
- Proper relationships with cascade deletes
- Timestamp mixins (created_at, updated_at)
- Database constraints (unique, check)

**Created Models:**
- `UserModel` - User accounts with authentication
- `CourseModel` - Courses with unique constraint per semester
- `LectureModel` - Lectures with week numbers (1-16), JSONB for key_concepts and embeddings
- `TestModel` - Tests with JSONB questions array
- `StudentAttemptModel` - Test attempts with JSONB answers and analytics

### 2. Domain Entities (Clean Architecture)

Pure business logic entities without infrastructure concerns:
- `User` - Business rules for activation/deactivation
- `Course` - Business rules for instructor updates
- `Lecture` - Rich business logic:
  - State transitions (pending → processing → completed)
  - Validation rules (min content length, key concepts)
  - Business queries (is_processed, is_ready_for_test_generation)

### 3. Repository Pattern

Implemented repositories with full CRUD operations:
- `UserRepository` - Create, get by ID/email, entity conversion
- `CourseRepository` - Create, get by ID/owner, update, delete
- `LectureRepository` - Create, get by ID/course, update, delete

All repositories:
- Accept domain entities
- Return domain entities
- Handle database model conversion internally
- Use async/await throughout

### 4. Database Connection

**File: `src/4_infrastructure/database/connection.py`**
- Async engine with NullPool (development)
- Async session factory
- `get_db()` dependency with automatic commit/rollback

### 5. Alembic Migrations

**File: `alembic/env.py`**
- Configured for async migrations
- Auto-imports all models
- Uses settings from config.py
- Ready for autogenerate

### 6. Health Check Endpoint

Updated `/health` endpoint to test database connectivity.

## 📁 File Structure

```
src/
├── 3_domain/entities/
│   ├── user.py          ✅ Business logic
│   ├── course.py        ✅ Business logic
│   └── lecture.py       ✅ Rich business logic with state machine
│
├── 4_infrastructure/database/
│   ├── connection.py    ✅ Async engine & session
│   ├── models/
│   │   ├── base.py      ✅ Base + TimestampMixin
│   │   ├── user.py      ✅ UserModel
│   │   ├── course.py    ✅ CourseModel
│   │   ├── lecture.py   ✅ LectureModel with JSONB
│   │   ├── test.py      ✅ TestModel with JSONB
│   │   └── student_attempt.py ✅ StudentAttemptModel
│   │
│   └── repositories/
│       ├── user_repository.py     ✅ Full CRUD
│       ├── course_repository.py   ✅ Full CRUD
│       └── lecture_repository.py  ✅ Full CRUD
│
└── core/
    └── dependencies.py  ✅ get_db() dependency

alembic/
└── env.py              ✅ Async migrations configured

scripts/
├── init_db.py          ✅ Initialize database
└── test_db_connection.py ✅ Test connectivity
```

## 🚀 How to Use

### 1. Setup PostgreSQL

```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb study_assistant
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Update `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/study_assistant
```

### 3. Install Dependencies

```bash
poetry install
```

### 4. Test Database Connection

```bash
poetry run python scripts/test_db_connection.py
```

### 5. Create Migration

```bash
# Generate migration from models
poetry run alembic revision --autogenerate -m "Initial schema"

# Apply migration
poetry run alembic upgrade head
```

### 6. Start Application

```bash
poetry run python src/main.py
```

Visit:
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

## 🎯 Key Features

### Clean Architecture Separation

**Domain Layer (Business Logic):**
```python
# Pure business logic, no database concerns
lecture = Lecture(id="lec_123", course_id="course_456", ...)
lecture.mark_as_processing()  # State transition
lecture.mark_as_completed(content, concepts, embeddings)
```

**Infrastructure Layer (Database):**
```python
# Repository handles persistence
repo = LectureRepository(session)
await repo.create(lecture)
await repo.update(lecture)
```

### Async Throughout

All database operations use async/await:
```python
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    return user
```

### JSONB for Flexibility

```python
# Lecture model stores flexible data
lecture.key_concepts = ["concept1", "concept2"]  # List
lecture.embedding_ids = ["emb_1", "emb_2"]       # List
lecture.metadata = {"source": "pdf", "pages": 10} # Dict
```

### Type Safety

All code has:
- Type hints on all functions
- Pydantic for validation (coming in Phase 3)
- SQLAlchemy 2.0 typed mappings

## 🧪 Testing Database

```python
# Test in Python REPL
import asyncio
from src.4_infrastructure.database.connection import async_session_maker
from src.4_infrastructure.database.repositories.user_repository import UserRepository
from src.3_domain.entities.user import User

async def test():
    async with async_session_maker() as session:
        # Create user
        user = User(
            id="user_test123",
            email="test@example.com",
            full_name="Test User"
        )
        
        repo = UserRepository(session)
        created = await repo.create(user, "hashed_password_here")
        print(f"Created: {created}")
        
        # Get user
        found = await repo.get_by_id(created.id)
        print(f"Found: {found}")
        
        await session.commit()

asyncio.run(test())
```

## 📊 Database Schema

```sql
-- Users table
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Courses table
CREATE TABLE courses (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) NOT NULL,
    semester VARCHAR(50) NOT NULL,
    instructor VARCHAR(200),
    owner_id VARCHAR REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(owner_id, code, semester)
);

-- Lectures table
CREATE TABLE lectures (
    id VARCHAR PRIMARY KEY,
    course_id VARCHAR REFERENCES courses(id) ON DELETE CASCADE,
    week_number INTEGER NOT NULL CHECK (week_number >= 1 AND week_number <= 16),
    title VARCHAR(200) NOT NULL,
    file_url VARCHAR,
    content TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    key_concepts JSONB DEFAULT '[]',
    embedding_ids JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(course_id, week_number)
);

-- Tests table
CREATE TABLE tests (
    id VARCHAR PRIMARY KEY,
    lecture_id VARCHAR REFERENCES lectures(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    total_points INTEGER DEFAULT 0,
    time_limit INTEGER DEFAULT 30,
    questions JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Student attempts table
CREATE TABLE student_attempts (
    id VARCHAR PRIMARY KEY,
    student_id VARCHAR REFERENCES users(id) ON DELETE CASCADE,
    test_id VARCHAR REFERENCES tests(id) ON DELETE CASCADE,
    total_score FLOAT DEFAULT 0.0,
    percentage FLOAT DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'in_progress',
    answers JSONB DEFAULT '[]',
    weak_topics JSONB DEFAULT '[]',
    analytics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## ✅ Phase 2 Checklist

- [x] Database models with SQLAlchemy 2.0
- [x] Domain entities with business logic
- [x] Repository pattern implementation
- [x] Async database connection
- [x] Alembic migrations setup
- [x] Health check with DB connectivity
- [x] Type hints throughout
- [x] Comprehensive docstrings
- [x] JSONB for flexible data
- [x] Database constraints
- [x] Test scripts

## 🎯 Ready for Phase 3: Authentication

Next phase will implement:
- User registration with password hashing
- JWT authentication
- Login/logout endpoints
- Protected routes
- Auth middleware

The database foundation is solid and ready!
