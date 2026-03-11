# AI Study Assistant Backend

Production-ready AI Study Assistant backend system using Python, FastAPI, and PostgreSQL.

## ✅ Project Status: COMPLETE

- ✅ Phase 1: Project Foundation & Structure
- ✅ Phase 2: Database Setup (PostgreSQL + SQLAlchemy 2.0)
- ✅ Phase 3: Authentication & Security (JWT + Bcrypt)
- ✅ Phase 4: Course Module (CRUD)
- ✅ Phase 5: Lecture Upload & File Storage
- ✅ Phase 6: AI Agents & RAG System
- ✅ Phase 7: Background Processing (Celery)
- ✅ Phase 8: Test Generation with RAG
- ✅ Phase 9: Test Submission & AI Evaluation

🎉 **All 9 phases completed!** See `PROJECT_COMPLETE.md` for full details.

## Features

- 🔐 JWT Authentication with bcrypt password hashing
- 📚 Course and lecture management
- � PDF lecture upload and processing
- � AI-powered test generation from lecture content
- 🧠 RAG (Retrieval-Augmented Generation) with pgvector
- ✅ Auto-grading (MCQ, True/False)
- 🎯 AI essay grading with detailed feedback
- 📊 Performance analytics and weak topic identification
- 💬 Personalized feedback in Mongolian
- ⚡ Background job processing with Celery
- 🏗️ Clean Architecture with 4 layers
- 🗄️ PostgreSQL with JSONB for flexible data

## Tech Stack

- Python 3.11+
- FastAPI 0.109+
- PostgreSQL 15+ with pgvector
- SQLAlchemy 2.0 (async)
- Alembic (migrations)
- JWT + Bcrypt (authentication)
- Celery + Redis (background jobs)
- OpenAI GPT-4
- Anthropic Claude Sonnet 4

## Quick Start

### 🚀 Компьютер Унтраагаад Дахин Асаахад

**Дэлгэрэнгүй заавар:** `STARTUP_GUIDE.md` файлыг үзнэ үү.

**Хурдан эхлүүлэх:**

```bash
# 1. Системийн статус шалгах
./startup.sh

# 2. Terminal 1 - FastAPI Server
cd ~/Documents/diplom/study-assistant-backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000

# 3. Terminal 2 - Celery Worker
cd ~/Documents/diplom/study-assistant-backend
source venv/bin/activate
celery -A src.infrastructure.queue.celery_app worker --loglevel=info
```

**Шалгах:**
- API Docs: http://127.0.0.1:8000/api/docs
- Health: http://127.0.0.1:8000/health

---

### 1. Install Dependencies

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies
poetry install
```

### 2. Setup PostgreSQL

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb study_assistant

# Enable pgvector extension
psql study_assistant -c "CREATE EXTENSION vector;"
```

### 3. Setup Redis

```bash
# macOS
brew install redis
brew services start redis

# Or with Docker
docker run -d -p 6379:6379 redis:alpine
```

### 4. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required settings:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/study_assistant
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Start Services

**Terminal 1: FastAPI**
```bash
uvicorn src.main:app --reload --port 8000
```

**Terminal 2: Celery Worker**
```bash
./scripts/run_celery.sh
```

**Terminal 3: Test Complete Flow**
```bash
python scripts/test_full_flow.py
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Complete API Flow

```bash
# 1. Register
POST /api/v1/auth/register

# 2. Login → Get JWT token
POST /api/v1/auth/login

# 3. Create course
POST /api/v1/courses

# 4. Upload lecture (triggers background processing)
POST /api/v1/lectures/upload

# 5. Check processing status
GET /api/v1/lectures/{lecture_id}/status

# 6. Generate AI test
POST /api/v1/tests/generate

# 7. Submit test answers
POST /api/v1/evaluations/submit/{test_id}

# 8. Get evaluation results
GET /api/v1/evaluations/attempt/{attempt_id}
```

See `QUICK_START.md` for detailed examples.

## Testing

```bash
# Test database
python scripts/test_db_connection.py

# Test authentication
python scripts/test_auth.py

# Test Celery
python scripts/test_celery.py

# Test complete flow
python scripts/test_full_flow.py
```

## Project Structure

```
src/
├── 1_presentation/    # API endpoints, schemas
├── 2_application/     # Use cases, orchestrators
├── 3_domain/         # Entities, agents, services
├── 4_infrastructure/ # Database, external services
├── config.py
└── main.py
```

## Documentation

- `PROJECT_COMPLETE.md` - Complete project overview
- `QUICK_START.md` - Quick start guide
- `PHASE[1-9]_COMPLETE.md` - Phase completion details
- `docs/` - Additional guides

## Key Features

### AI-Powered
- Lecture comprehension with key concept extraction
- RAG-based test generation
- AI essay grading with rubrics
- Personalized feedback generation

### Background Processing
- Async lecture processing with Celery
- Automatic retries on failure
- Status tracking
- Scalable worker architecture

### Analytics
- Performance metrics by difficulty
- Performance metrics by question type
- Weak topic identification
- Attempt history tracking

## Deployment

Ready for deployment to:
- Railway
- Render
- Heroku
- AWS ECS
- Google Cloud Run
- DigitalOcean

See deployment guides in `docs/` folder.

## Contributing

This is a complete, production-ready system. Feel free to:
- Add new features
- Improve existing functionality
- Write tests
- Enhance documentation

## License

MIT License - See LICENSE file for details

---

Built with ❤️ using Clean Architecture principles

🎉 **Project Complete!** All 9 phases implemented and tested.
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb study_assistant
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Update `.env`:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/study_assistant
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-change-in-production
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
```

### 4. Initialize Database

```bash
# Test connection
poetry run python scripts/test_db_connection.py

# Create tables
poetry run alembic revision --autogenerate -m "Initial schema"
poetry run alembic upgrade head

# (Optional) Create sample data
poetry run python scripts/create_sample_data.py
```

### 5. Start Application

```bash
poetry run python src/main.py
```

Visit:
- API Docs: http://localhost:8000/api/docs
- Health Check: http://localhost:8000/health

## 🔐 Authentication

### Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Access Protected Endpoints

```bash
TOKEN="your_token_here"
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Test Authentication

```bash
poetry run python scripts/test_auth.py
```

## Architecture

Clean Architecture with 4 layers:

### Layer 1: Presentation (1_presentation/)
- FastAPI routes, schemas, middleware
- Request/response validation with Pydantic
- JWT authentication endpoints

### Layer 2: Application (2_application/)
- Use cases (business operations)
- RegisterUserUseCase, LoginUserUseCase
- Agent orchestrators (multi-agent workflows)

### Layer 3: Domain (3_domain/)
- Domain entities with business logic
- AI Agents (comprehension, test generation, evaluation)
- Business rules and interfaces

### Layer 4: Infrastructure (4_infrastructure/)
- Database (PostgreSQL + SQLAlchemy)
- LLM adapters (OpenAI, Claude)
- File storage and processors
- Background jobs (Celery)

## Database Schema

```
users → courses → lectures → tests → student_attempts
```

All tables use:
- String-based UUIDs (e.g., `user_abc123`)
- JSONB for flexible data
- Timestamps (created_at, updated_at)
- Cascade deletes

## Development

### Run Tests
```bash
poetry run pytest
```

### Format Code
```bash
poetry run black .
poetry run ruff check .
```

### Database Migrations
```bash
# Create migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

### Useful Scripts
```bash
# Test database connection
poetry run python scripts/test_db_connection.py

# Initialize database (drops and recreates)
poetry run python scripts/init_db.py

# Create sample data
poetry run python scripts/create_sample_data.py

# Test authentication
poetry run python scripts/test_auth.py
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/health

### Available Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | No | Register new user |
| POST | `/api/v1/auth/login` | No | Login and get JWT token |
| GET | `/api/v1/auth/me` | Yes | Get current user info |

## Project Structure

```
study-assistant-backend/
├── src/
│   ├── 1_presentation/      # API routes, schemas
│   ├── 2_application/        # Use cases, orchestrators
│   ├── 3_domain/            # Entities, agents, rules
│   ├── 4_infrastructure/    # Database, external APIs
│   ├── core/                # Security, dependencies
│   ├── config.py            # Settings
│   └── main.py              # FastAPI app
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
└── docs/                    # Documentation
```

## Documentation

- [Setup Guide](SETUP_GUIDE.md) - Initial setup instructions
- [Phase 2 Complete](PHASE2_COMPLETE.md) - Database implementation
- [Phase 3 Complete](PHASE3_COMPLETE.md) - Authentication implementation
- [Database Guide](docs/DATABASE_GUIDE.md) - Database usage patterns
- [Auth Guide](docs/AUTH_GUIDE.md) - Authentication usage guide

## Protecting Your Endpoints

```python
from fastapi import APIRouter
from src.core.dependencies import CurrentUser

router = APIRouter()

@router.get("/protected")
async def protected_route(current_user: CurrentUser):
    """This endpoint requires JWT authentication."""
    return {
        "message": f"Hello {current_user.full_name}!",
        "user_id": current_user.id
    }
```

## Contributing

This project follows:
- Clean Architecture principles
- SOLID principles
- Repository pattern
- Async/await throughout
- Type hints on all functions
- Comprehensive docstrings

## Security

- ✅ Bcrypt password hashing
- ✅ JWT token authentication
- ✅ Token expiration (30 minutes)
- ✅ Active user validation
- ✅ No passwords in responses
- ⚠️ Use HTTPS in production
- ⚠️ Change secrets in production

## License

MIT
# diplom_backend
# diplom_backend
