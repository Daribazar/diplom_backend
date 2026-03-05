# AI Study Assistant Backend - Setup Guide

## ✅ Phase 1 Complete: Project Foundation

The complete folder structure and initial files have been created following Clean Architecture principles.

## 📁 Project Structure Overview

```
study-assistant-backend/
├── src/
│   ├── 1_presentation/      # API Layer (FastAPI routes, schemas, middleware)
│   ├── 2_application/        # Business Logic (Use cases, orchestrators)
│   ├── 3_domain/            # Core Domain (Entities, agents, rules)
│   ├── 4_infrastructure/    # External Systems (Database, LLM, storage)
│   ├── core/                # Shared utilities
│   ├── config.py            # Configuration
│   └── main.py              # FastAPI entry point
├── alembic/                 # Database migrations
├── tests/                   # Test suite
└── Configuration files
```

## 🏗️ Architecture Layers

### Layer 1: Presentation (1_presentation/)
- API endpoints (auth, courses, lectures, tests, evaluations)
- Pydantic schemas for validation
- Middleware (CORS, logging, error handling)

### Layer 2: Application (2_application/)
- Use cases (business operations)
- Agent orchestrators (multi-agent workflows)

### Layer 3: Domain (3_domain/)
- Domain entities (User, Course, Lecture, Test)
- AI Agents (comprehension, test generation, evaluation, recommendations)
- Business rules and interfaces
- Memory system for agents

### Layer 4: Infrastructure (4_infrastructure/)
- Database (PostgreSQL + SQLAlchemy models)
- LLM adapters (OpenAI, Claude)
- File storage (local, S3)
- File processors (PDF, DOCX)
- Background jobs (Celery)
- Caching (Redis)

## 🚀 Next Steps

### Phase 2: Database Setup
- Configure PostgreSQL with pgvector extension
- Implement database connection
- Create Alembic migrations
- Test database connectivity

### Phase 3: Authentication Module
- Implement user registration
- Implement user login with JWT
- Add authentication middleware
- Create auth endpoints

### Phase 4: Course Module
- Implement course CRUD operations
- Add course endpoints
- Add authorization checks

### Phase 5: Lecture Module
- Implement file upload
- Add PDF/DOCX processing
- Implement semantic chunking
- Generate embeddings with pgvector

### Phase 6: Agent System
- Implement LLM adapters (OpenAI, Claude)
- Create lecture comprehension agent
- Build agent memory system
- Implement RAG (Retrieval Augmented Generation)

### Phase 7: Test Generation
- Implement test generator agent
- Create test generation endpoints
- Add question validation

### Phase 8: Evaluation & Recommendations
- Implement evaluation agent
- Add recommendation agent
- Create evaluation endpoints

### Phase 9: Background Jobs
- Configure Celery workers
- Implement async lecture processing
- Add job monitoring

## 📦 Installation

1. Install Poetry (if not installed):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Install dependencies:
```bash
poetry install
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Update `.env` with your credentials:
- Database URL
- OpenAI API key
- Anthropic API key
- JWT secrets

## 🔧 Development Commands

Start development server:
```bash
poetry run python src/main.py
```

Run tests:
```bash
poetry run pytest
```

Format code:
```bash
poetry run black .
```

Lint code:
```bash
poetry run ruff check .
```

## 📝 Key Principles Followed

✅ Clean Architecture (4 layers)
✅ Dependency Injection
✅ Repository Pattern
✅ SOLID principles
✅ Async/await throughout
✅ Type hints everywhere
✅ Comprehensive docstrings
✅ Pydantic v2 validation
✅ SQLAlchemy 2.0 async

## 🎯 Ready for Phase 2

The foundation is complete. You can now proceed with Phase 2: Database Setup.

All files are created with proper structure, imports, and placeholder implementations marked with TODO comments for each phase.
