# Phase 7: Background Processing with Celery - COMPLETE ✅

## Overview
Implemented asynchronous background processing for lecture analysis using Celery + Redis. Lecture processing now happens in background workers, allowing immediate API responses.

## Components Implemented

### 1. Celery Application Setup
**File: `src/4_infrastructure/queue/celery_app.py`**
- Celery app configuration with Redis broker
- Task serialization (JSON)
- Task routing to specific queues
- Timeouts and retry policies
- Worker configuration

**Configuration:**
```python
- Task time limit: 30 minutes
- Soft time limit: 25 minutes
- Max retries: 3
- Retry delay: Exponential backoff (2^n seconds)
- Queue: lecture_processing
```

### 2. Background Tasks
**File: `src/4_infrastructure/queue/tasks/lecture_processing.py`**

**AsyncTask Base Class:**
- Custom Celery task for async functions
- Runs async code in event loop
- Enables async database operations

**process_lecture_task:**
- Processes lecture with AI agents
- Extracts key concepts
- Creates embeddings
- Updates lecture status
- Automatic retry on failure
- Comprehensive error handling

**test_celery_task:**
- Simple test task for verification
- Tests Celery + Redis connectivity

### 3. Updated Upload Flow
**File: `src/2_application/usecases/lecture/upload_lecture.py`**

**New Flow:**
1. Validate course ownership
2. Check for duplicates
3. Upload PDF to storage
4. Extract text content
5. Create lecture record (status: "pending")
6. **Trigger Celery task** (async processing)
7. Return immediately to user

**Before (Phase 6):**
- Synchronous processing
- User waits 2-3 minutes
- Blocks API thread

**After (Phase 7):**
- Asynchronous processing
- User gets immediate response
- Background worker handles processing

### 4. Status Tracking
**New Endpoint: `GET /api/v1/lectures/{lecture_id}/status`**

Returns:
```json
{
    "lecture_id": "lec_abc123",
    "title": "Introduction to AI",
    "status": "processing",
    "key_concepts": [],
    "created_at": "2026-03-05T21:43:21Z",
    "processed_at": null
}
```

**Status Values:**
- `pending`: Waiting in queue
- `processing`: Currently being processed
- `completed`: Successfully processed
- `failed`: Processing failed (will retry)

### 5. Worker Scripts
**File: `scripts/run_celery.sh`**
- Starts Celery worker
- 2 concurrent workers
- Listens to lecture_processing queue
- Info-level logging

**File: `scripts/test_celery.py`**
- Tests Celery connectivity
- Verifies Redis connection
- Runs simple test task

## Architecture

### System Components
```
┌─────────────┐
│   FastAPI   │ ← User uploads PDF
└──────┬──────┘
       │
       ├─→ Save to DB (status: pending)
       │
       └─→ Celery Task Queue (Redis)
                  │
                  ↓
           ┌──────────────┐
           │ Celery Worker│
           └──────┬───────┘
                  │
                  ├─→ Extract text (PDF)
                  ├─→ AI comprehension (LLM)
                  ├─→ Create embeddings (OpenAI)
                  ├─→ Store in pgvector
                  └─→ Update DB (status: completed)
```

### Task Lifecycle
```
1. User uploads PDF
   ↓
2. API creates lecture (pending)
   ↓
3. Task queued in Redis
   ↓
4. Worker picks up task
   ↓
5. Status → processing
   ↓
6. AI processing (2-3 min)
   ↓
7. Status → completed
   ↓
8. User polls /status endpoint
```

## API Endpoints

### Upload Lecture (Updated)
```http
POST /api/v1/lectures/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

course_id: course_abc123
week_number: 1
title: Introduction to AI
file: @lecture.pdf

Response (Immediate):
{
    "id": "lec_abc123",
    "course_id": "course_abc123",
    "week_number": 1,
    "title": "Introduction to AI",
    "status": "pending",
    "message": "Lecture uploaded successfully. Processing in background.",
    "estimated_time": "2-3 minutes"
}
```

### Check Status (New)
```http
GET /api/v1/lectures/{lecture_id}/status
Authorization: Bearer <token>

Response:
{
    "lecture_id": "lec_abc123",
    "title": "Introduction to AI",
    "status": "completed",
    "key_concepts": [
        "Machine Learning Basics",
        "Neural Networks",
        "Deep Learning"
    ],
    "created_at": "2026-03-05T21:43:21Z",
    "processed_at": "2026-03-05T21:45:30Z"
}
```

### Process Manually (Phase 6 - Still Available)
```http
POST /api/v1/lectures/{lecture_id}/process
Authorization: Bearer <token>

Response:
{
    "message": "Lecture processed successfully",
    "lecture_id": "lec_abc123",
    "key_concepts": [...],
    "chunks_created": 5,
    "llm_usage": {...}
}
```

## Running the System

### Prerequisites
```bash
# Install dependencies
poetry install

# Start Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:alpine
```

### Terminal 1: FastAPI Server
```bash
uvicorn src.main:app --reload --port 8000
```

### Terminal 2: Celery Worker
```bash
./scripts/run_celery.sh

# Or manually:
celery -A src.4_infrastructure.queue.celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=lecture_processing
```

### Terminal 3: Test Celery
```bash
python scripts/test_celery.py
```

## Testing

### 1. Test Celery Connectivity
```bash
python scripts/test_celery.py

Expected Output:
Testing Celery task...
Task ID: abc-123-def-456
Task State: SUCCESS
Result: 15
✅ Celery is working!
```

### 2. Test Lecture Upload
```bash
# Upload lecture
curl -X POST http://localhost:8000/api/v1/lectures/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "course_id=course_abc123" \
  -F "week_number=1" \
  -F "title=Test Lecture" \
  -F "file=@lecture.pdf"

# Response: status="pending"
```

### 3. Monitor Celery Logs
```
[2026-03-05 21:43:21,123: INFO] Task lecture_processing.process_lecture[abc-123] received
[2026-03-05 21:43:21,456: INFO] Starting lecture processing: lec_abc123
[2026-03-05 21:45:30,789: INFO] Lecture processing completed: lec_abc123
[2026-03-05 21:45:30,890: INFO] Task lecture_processing.process_lecture[abc-123] succeeded
```

### 4. Check Status
```bash
curl -X GET http://localhost:8000/api/v1/lectures/lec_abc123/status \
  -H "Authorization: Bearer YOUR_TOKEN"

# Response: status="completed"
```

## Error Handling

### Automatic Retries
- Task fails → Retry 1 (after 2 seconds)
- Task fails → Retry 2 (after 4 seconds)
- Task fails → Retry 3 (after 8 seconds)
- Task fails → Status set to "failed"

### Failure Scenarios
1. **LLM API Error**: Retries with backoff
2. **Database Error**: Retries with backoff
3. **Timeout**: Task killed after 30 minutes
4. **Worker Crash**: Task requeued automatically

## Configuration

### Celery Settings
```python
# src/4_infrastructure/queue/celery_app.py
task_time_limit = 30 * 60  # 30 minutes
task_soft_time_limit = 25 * 60  # 25 minutes
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000
```

### Redis Settings
```bash
# .env
REDIS_URL=redis://localhost:6379/0
```

## Performance Benefits

### Before (Synchronous)
- Upload time: 2-3 minutes
- Blocks API thread
- Poor user experience
- Limited concurrency

### After (Asynchronous)
- Upload time: < 1 second
- Non-blocking
- Excellent user experience
- Unlimited concurrency (scale workers)

## Monitoring

### Celery Flower (Optional)
```bash
# Install
pip install flower

# Run
celery -A src.4_infrastructure.queue.celery_app flower

# Access: http://localhost:5555
```

### Redis CLI
```bash
redis-cli

# Check queue length
LLEN celery

# Check task results
KEYS celery-task-meta-*
```

## Files Created/Modified

### Created (7 files)
1. `src/4_infrastructure/queue/__init__.py`
2. `src/4_infrastructure/queue/celery_app.py`
3. `src/4_infrastructure/queue/tasks/__init__.py`
4. `src/4_infrastructure/queue/tasks/lecture_processing.py`
5. `scripts/run_celery.sh`
6. `scripts/test_celery.py`
7. `PHASE7_COMPLETE.md`

### Modified (2 files)
1. `src/2_application/usecases/lecture/upload_lecture.py` - Added Celery task trigger
2. `src/1_presentation/api/v1/endpoints/lectures.py` - Added status endpoint

## Test Checklist

- ✅ Upload lecture → status: "pending"
- ✅ Celery picks up task
- ✅ PDF text extracted
- ✅ AI comprehension runs
- ✅ Embeddings stored in pgvector
- ✅ Lecture status → "completed"
- ✅ Key concepts extracted
- ✅ Status endpoint returns correct data
- ✅ Automatic retry on failure
- ✅ Error handling and logging

## Next Steps (Phase 8)
- Test Generator Agent implementation
- Evaluation Agent implementation
- Test generation endpoint
- Test submission endpoint
- Student attempt tracking

## Status: ✅ COMPLETE
Phase 7 implementation is complete. Background processing with Celery is fully functional.
