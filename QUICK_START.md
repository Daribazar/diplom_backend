# Quick Start Guide - AI Study Assistant Backend

## Prerequisites
- Python 3.11+
- PostgreSQL with pgvector extension
- Redis
- OpenAI API key
- Anthropic API key (optional)

## Installation

### 1. Clone and Install Dependencies
```bash
# Install dependencies
poetry install

# Or with pip
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required settings:**
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/study_assistant
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
```

### 3. Setup Database
```bash
# Create database
createdb study_assistant

# Run migrations
alembic upgrade head

# Initialize with sample data (optional)
python scripts/init_db.py
python scripts/create_sample_data.py
```

### 4. Start Services

**Terminal 1: Redis**
```bash
redis-server
```

**Terminal 2: FastAPI**
```bash
uvicorn src.main:app --reload --port 8000
```

**Terminal 3: Celery Worker**
```bash
./scripts/run_celery.sh
```

## Test the System

### 1. Test Database Connection
```bash
python scripts/test_db_connection.py
```

### 2. Test Celery
```bash
python scripts/test_celery.py
```

### 3. Test Authentication
```bash
python scripts/test_auth.py
```

### 4. Test API
```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Use the access_token from login response for authenticated requests
```

## API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Common Commands

### Database
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Development
```bash
# Run tests
pytest

# Format code
black src/

# Lint
ruff check src/
```

### Celery
```bash
# Start worker
./scripts/run_celery.sh

# Monitor with Flower (optional)
pip install flower
celery -A src.4_infrastructure.queue.celery_app flower
# Visit: http://localhost:5555
```

## Project Structure
```
src/
├── 1_presentation/     # API endpoints, schemas
├── 2_application/      # Use cases, orchestrators
├── 3_domain/          # Entities, agents, services
├── 4_infrastructure/  # Database, external services
├── config.py          # Configuration
└── main.py           # FastAPI app

scripts/               # Utility scripts
alembic/              # Database migrations
tests/                # Test files
```

## Workflow Example

### Upload and Process Lecture
```bash
# 1. Create course
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Machine Learning 101",
    "description": "Introduction to ML"
  }'

# 2. Upload lecture (triggers background processing)
curl -X POST http://localhost:8000/api/v1/lectures/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "course_id=course_abc123" \
  -F "week_number=1" \
  -F "title=Introduction to ML" \
  -F "file=@lecture.pdf"

# 3. Check processing status
curl -X GET http://localhost:8000/api/v1/lectures/lec_abc123/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. Get course lectures
curl -X GET http://localhost:8000/api/v1/lectures/course/course_abc123 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql -l | grep study_assistant
```

### Redis Connection Error
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

### Celery Worker Not Processing
```bash
# Check Redis queue
redis-cli LLEN celery

# Check worker logs
./scripts/run_celery.sh
```

### Migration Issues
```bash
# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head
```

## Development Tips

1. **Use API docs**: Visit `/docs` for interactive API testing
2. **Check logs**: Celery worker shows processing progress
3. **Monitor Redis**: Use `redis-cli` to inspect queues
4. **Test incrementally**: Test each phase before moving to next
5. **Use sample data**: Run `create_sample_data.py` for testing

## Next Steps
- Phase 8: Test generation and evaluation
- Phase 9: Recommendation system
- Phase 10: Production deployment

## Support
Check the phase completion documents for detailed information:
- PHASE2_COMPLETE.md - Database setup
- PHASE3_COMPLETE.md - Authentication
- PHASE4_COMPLETE.md - Course CRUD
- PHASE5_COMPLETE.md - Lecture upload
- PHASE6_COMPLETE.md - AI agents
- PHASE7_COMPLETE.md - Background processing
