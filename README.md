# AI Study Assistant Backend

Production-ready AI Study Assistant backend system using Python, FastAPI, and PostgreSQL.

## ✅ Current Status

- ✅ Phase 1: Project Foundation & Structure
- ✅ Phase 2: Database Setup (PostgreSQL + SQLAlchemy 2.0)
- ✅ Phase 3: Authentication & Security (JWT + Bcrypt)
- 🔄 Phase 4: Course Module (Next)

## Features

- 🔐 JWT Authentication with bcrypt password hashing
- 📚 Course and lecture management
- 🤖 AI-generated tests based on lecture content
- 📊 Personalized study recommendations
- 🧠 Multi-agent AI system with memory
- 🏗️ Clean Architecture with 4 layers
- ⚡ Async/await throughout
- 🗄️ PostgreSQL with JSONB for flexible data

## Tech Stack

- Python 3.11+
- FastAPI 0.109+
- PostgreSQL 15+
- SQLAlchemy 2.0 (async)
- Alembic (migrations)
- JWT + Bcrypt (authentication)
- Celery + Redis (background jobs)
- OpenAI GPT-4
- Anthropic Claude Sonnet

## Quick Start

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
