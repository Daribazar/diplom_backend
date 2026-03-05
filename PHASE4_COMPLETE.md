# Phase 4 Complete: Course Module - CRUD Operations ✅

## What Was Implemented

### ✅ Complete Course Management System

**Duration:** Phase 4
**Status:** Complete and Production-Ready

## 📦 Deliverables

### 1. Pydantic Schemas (`src/1_presentation/schemas/course.py`)

**Request Schemas:**
- ✅ `CourseCreate` - Create course with name, code, semester, instructor
- ✅ `CourseUpdate` - Update course (all fields optional)

**Response Schemas:**
- ✅ `CourseResponse` - Single course response
- ✅ `CourseListResponse` - List of courses with total count

**Features:**
- Field validation (min/max length)
- Example data in schema
- Type safety with Pydantic v2

### 2. Use Cases (Business Logic)

**CreateCourseUseCase:**
- ✅ Generate UUID for course
- ✅ Create domain entity
- ✅ Persist to database
- ✅ Return created course

**GetCoursesUseCase:**
- ✅ Get all courses for owner
- ✅ Sorted by creation date (newest first)
- ✅ Returns list of domain entities

**GetCourseUseCase:**
- ✅ Get single course by ID
- ✅ Ownership validation
- ✅ Raises NotFoundError if not exists
- ✅ Raises UnauthorizedError if not owner

**UpdateCourseUseCase:**
- ✅ Get existing course
- ✅ Ownership validation
- ✅ Update fields (name, code, instructor)
- ✅ Use domain method for instructor update
- ✅ Persist changes

**DeleteCourseUseCase:**
- ✅ Get existing course
- ✅ Ownership validation
- ✅ Delete course (cascade to lectures, tests, attempts)
- ✅ Return success status

### 3. Repository Updates

**CourseRepository:**
- ✅ `create()` - Create course
- ✅ `get_by_id()` - Get by ID
- ✅ `get_by_owner()` - Get all for user
- ✅ `update()` - Update course
- ✅ `delete()` - Delete course
- ✅ `_to_entity()` - Convert model to entity

### 4. API Endpoints

**POST /api/v1/courses**
- Create new course
- Requires authentication
- Returns 201 Created
- Returns CourseResponse

**GET /api/v1/courses**
- Get all courses for current user
- Requires authentication
- Returns CourseListResponse
- Sorted by creation date

**GET /api/v1/courses/{course_id}**
- Get single course by ID
- Requires authentication
- Ownership validation
- Returns 404 if not found
- Returns 403 if not owner

**PATCH /api/v1/courses/{course_id}**
- Update course
- Requires authentication
- Ownership validation
- All fields optional
- Returns updated course

**DELETE /api/v1/courses/{course_id}**
- Delete course
- Requires authentication
- Ownership validation
- Returns 204 No Content
- Cascade deletes related data

### 5. Testing Script

- ✅ `scripts/test_courses.py` - Complete CRUD test
- Tests all 5 endpoints
- Tests authorization
- Tests error cases
- Clear output messages

## 🔐 Security Features

### Authorization
- All endpoints require JWT authentication
- Ownership validation on get/update/delete
- Users can only access their own courses
- Proper error responses (401, 403, 404)

### Data Validation
- Pydantic validation on all inputs
- Field length constraints
- Type safety throughout
- Optional fields handled correctly

## 📊 API Flow

```
1. Create Course:
   User (with token) → POST /courses → Validate → Create → Return Course

2. List Courses:
   User (with token) → GET /courses → Get by owner → Return List

3. Get Course:
   User (with token) → GET /courses/{id} → Check ownership → Return Course

4. Update Course:
   User (with token) → PATCH /courses/{id} → Check ownership → Update → Return Course

5. Delete Course:
   User (with token) → DELETE /courses/{id} → Check ownership → Delete → 204
```

## 🚀 How to Use

### 1. Start the Server

```bash
poetry run python src/main.py
```

### 2. Test with Swagger UI

Visit: http://localhost:8000/api/docs

**Create Course:**
```json
POST /api/v1/courses
Authorization: Bearer <token>
{
  "name": "Introduction to Machine Learning",
  "code": "CS401",
  "semester": "Fall 2024",
  "instructor": "Prof. Smith"
}
```

**Get All Courses:**
```
GET /api/v1/courses
Authorization: Bearer <token>
```

**Update Course:**
```json
PATCH /api/v1/courses/{course_id}
Authorization: Bearer <token>
{
  "name": "Advanced Machine Learning",
  "instructor": "Prof. Johnson"
}
```

**Delete Course:**
```
DELETE /api/v1/courses/{course_id}
Authorization: Bearer <token>
```

### 3. Test with Script

```bash
poetry run python scripts/test_courses.py
```

Expected output:
```
🧪 Testing Course CRUD Operations

1️⃣ Setting up authentication...
   ✅ Authentication successful

2️⃣ Testing course creation (POST /courses)...
   ✅ Course created: Introduction to Machine Learning
   Course ID: course_abc123

3️⃣ Testing get all courses (GET /courses)...
   ✅ Retrieved 1 course(s)

4️⃣ Testing get single course (GET /courses/course_abc123)...
   ✅ Retrieved course: Introduction to Machine Learning

5️⃣ Testing course update (PATCH /courses/course_abc123)...
   ✅ Course updated

6️⃣ Testing authorization (invalid token)...
   ✅ Unauthorized access correctly rejected

7️⃣ Testing course deletion (DELETE /courses/course_abc123)...
   ✅ Course deleted successfully

8️⃣ Verifying course was deleted...
   ✅ Course not found (correctly deleted)

✅ All course CRUD tests passed!
```

### 4. Use in Your Code

```python
from fastapi import APIRouter, Depends
from src.core.dependencies import CurrentUser, get_db
from src.4_infrastructure.database.repositories.course_repository import CourseRepository
from src.2_application.usecases.course.get_courses import GetCoursesUseCase

router = APIRouter()

@router.get("/my-courses")
async def get_my_courses(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db)
):
    """Get courses for authenticated user."""
    repo = CourseRepository(db)
    use_case = GetCoursesUseCase(repo)
    courses = await use_case.execute(current_user.id)
    return {"courses": courses}
```

## 📁 Files Created/Modified

### New Files (6)
```
src/2_application/usecases/course/
├── get_course.py            ✅ Get single course
└── update_course.py         ✅ Update course

scripts/
└── test_courses.py          ✅ CRUD testing script

PHASE4_COMPLETE.md           ✅ This file
```

### Modified Files (7)
```
src/1_presentation/
├── api/v1/router.py         ✅ Include course routes
├── api/v1/endpoints/courses.py ✅ All CRUD endpoints
└── schemas/course.py        ✅ Request/response schemas

src/2_application/usecases/course/
├── create_course.py         ✅ Create logic
├── get_courses.py           ✅ List logic
└── delete_course.py         ✅ Delete logic

src/4_infrastructure/database/repositories/
└── course_repository.py     ✅ Update method added
```

## 🧪 Testing

### Manual Testing with cURL

**Create Course:**
```bash
TOKEN="your_token_here"
curl -X POST http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Data Structures",
    "code": "CS201",
    "semester": "Spring 2024",
    "instructor": "Prof. Brown"
  }'
```

**Get All Courses:**
```bash
curl -X GET http://localhost:8000/api/v1/courses \
  -H "Authorization: Bearer $TOKEN"
```

**Update Course:**
```bash
curl -X PATCH http://localhost:8000/api/v1/courses/course_abc123 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instructor": "Prof. Davis"
  }'
```

**Delete Course:**
```bash
curl -X DELETE http://localhost:8000/api/v1/courses/course_abc123 \
  -H "Authorization: Bearer $TOKEN"
```

### Automated Testing

```bash
# Run course test script
poetry run python scripts/test_courses.py

# Run with pytest (when tests are added)
poetry run pytest tests/integration/api/test_courses.py
```

## 🎯 Key Features

### Clean Architecture Compliance
- ✅ Use cases contain business logic
- ✅ Domain entities remain pure
- ✅ Repository pattern for data access
- ✅ Dependency injection throughout

### Security & Authorization
- ✅ JWT authentication required
- ✅ Ownership validation
- ✅ Proper error responses
- ✅ No data leakage

### Developer Experience
- ✅ Type-safe with Pydantic
- ✅ Clear error messages
- ✅ Swagger UI integration
- ✅ Testing utilities
- ✅ Example data in schemas

## 📚 API Documentation

### Swagger UI

Visit http://localhost:8000/api/docs for interactive API documentation.

### Endpoints Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/courses` | Yes | Create new course |
| GET | `/api/v1/courses` | Yes | Get all user's courses |
| GET | `/api/v1/courses/{id}` | Yes | Get single course |
| PATCH | `/api/v1/courses/{id}` | Yes | Update course |
| DELETE | `/api/v1/courses/{id}` | Yes | Delete course |

## ✅ Quality Checklist

- [x] All CRUD operations implemented
- [x] Authentication required
- [x] Ownership validation
- [x] Pydantic validation
- [x] Type hints throughout
- [x] Comprehensive docstrings
- [x] Error handling
- [x] Testing script
- [x] API documentation
- [x] Clean Architecture compliance
- [x] Repository pattern
- [x] Use cases for business logic

## 🎯 Next Steps: Phase 5 - Lecture Module

Ready to implement:
1. Lecture upload (PDF, DOCX)
2. File storage (local/S3)
3. File processing
4. Lecture CRUD operations
5. Lecture listing by course
6. Protected lecture routes

The course module is solid and ready for lectures!

## 💡 Usage Examples

### Creating a Course

```python
from src.2_application.usecases.course.create_course import CreateCourseUseCase
from src.4_infrastructure.database.repositories.course_repository import CourseRepository

async def create_course_example(db: AsyncSession, user_id: str):
    repo = CourseRepository(db)
    use_case = CreateCourseUseCase(repo)
    
    course = await use_case.execute(
        name="Algorithms",
        code="CS301",
        semester="Fall 2024",
        owner_id=user_id,
        instructor="Prof. Wilson"
    )
    
    return course
```

### Updating a Course

```python
from src.2_application.usecases.course.update_course import UpdateCourseUseCase

async def update_course_example(db: AsyncSession, course_id: str, user_id: str):
    repo = CourseRepository(db)
    use_case = UpdateCourseUseCase(repo)
    
    course = await use_case.execute(
        course_id=course_id,
        user_id=user_id,
        name="Advanced Algorithms",
        instructor="Prof. Taylor"
    )
    
    return course
```

### Authorization Pattern

```python
# This pattern is used in all endpoints
course = await repo.get_by_id(course_id)

if not course:
    raise NotFoundError("Course not found")

if course.owner_id != user_id:
    raise UnauthorizedError("Not authorized")

# Proceed with operation...
```

## 🎉 Phase 4 Status: COMPLETE

All objectives achieved. Course module is production-ready with complete CRUD operations, authentication, and authorization.

**Ready for Phase 5: Lecture Module Implementation**
