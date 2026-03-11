# AI Study Assistant - API Endpoints

**Base URL:** `http://127.0.0.1:8000/api/v1`

**API Documentation:** http://127.0.0.1:8000/api/docs

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [Courses](#courses)
3. [Lectures](#lectures)
4. [Tests](#tests)
5. [Evaluations](#evaluations)

---

## 🔐 Authentication

### 1. Register User
**POST** `/auth/register`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "user_abc123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }'
```

---

### 2. Login User
**POST** `/auth/login`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

---

### 3. Get Current User Info
**GET** `/auth/me`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": "user_abc123",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 📚 Courses

### 1. Create Course
**POST** `/courses`

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Introduction to AI",
  "code": "CS101",
  "semester": "Spring 2024",
  "instructor": "Prof. Smith"
}
```

**Response (201):**
```json
{
  "id": "course_xyz789",
  "name": "Introduction to AI",
  "code": "CS101",
  "semester": "Spring 2024",
  "instructor": "Prof. Smith",
  "owner_id": "user_abc123",
  "created_at": "2024-03-06T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/courses" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Introduction to AI",
    "code": "CS101",
    "semester": "Spring 2024",
    "instructor": "Prof. Smith"
  }'
```

---

### 2. Get All Courses
**GET** `/courses`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "total": 2,
  "courses": [
    {
      "id": "course_xyz789",
      "name": "Introduction to AI",
      "code": "CS101",
      "semester": "Spring 2024",
      "instructor": "Prof. Smith",
      "owner_id": "user_abc123",
      "created_at": "2024-03-06T12:00:00Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/courses" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 3. Get Single Course
**GET** `/courses/{course_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": "course_xyz789",
  "name": "Introduction to AI",
  "code": "CS101",
  "semester": "Spring 2024",
  "instructor": "Prof. Smith",
  "owner_id": "user_abc123",
  "created_at": "2024-03-06T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/courses/course_xyz789" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 4. Update Course
**PATCH** `/courses/{course_id}`

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Advanced AI",
  "instructor": "Prof. Johnson"
}
```

**Response (200):**
```json
{
  "id": "course_xyz789",
  "name": "Advanced AI",
  "code": "CS101",
  "semester": "Spring 2024",
  "instructor": "Prof. Johnson",
  "owner_id": "user_abc123",
  "created_at": "2024-03-06T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X PATCH "http://127.0.0.1:8000/api/v1/courses/course_xyz789" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Advanced AI",
    "instructor": "Prof. Johnson"
  }'
```

---

### 5. Delete Course
**DELETE** `/courses/{course_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (204):** No Content

**cURL Example:**
```bash
curl -X DELETE "http://127.0.0.1:8000/api/v1/courses/course_xyz789" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 📖 Lectures

### 1. Upload Lecture
**POST** `/lectures/upload`

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Form Data:**
- `course_id`: string (required)
- `week_number`: integer (1-16, required)
- `title`: string (required)
- `file`: PDF file (required, max 10MB)

**Response (201):**
```json
{
  "id": "lec_def456",
  "course_id": "course_xyz789",
  "week_number": 1,
  "title": "Introduction to Neural Networks",
  "status": "pending",
  "message": "Lecture uploaded successfully. Processing in background.",
  "estimated_time": "2-3 minutes"
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/lectures/upload" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "course_id=course_xyz789" \
  -F "week_number=1" \
  -F "title=Introduction to Neural Networks" \
  -F "file=@/path/to/lecture.pdf"
```

**Postman Setup:**
1. Method: POST
2. URL: `http://127.0.0.1:8000/api/v1/lectures/upload`
3. Headers: `Authorization: Bearer YOUR_TOKEN`
4. Body: form-data
   - course_id: course_xyz789
   - week_number: 1
   - title: Introduction to Neural Networks
   - file: [Select PDF file]

---

### 2. Get Course Lectures
**GET** `/lectures/course/{course_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "total": 1,
  "lectures": [
    {
      "id": "lec_def456",
      "course_id": "course_xyz789",
      "week_number": 1,
      "title": "Introduction to Neural Networks",
      "status": "completed",
      "key_concepts": ["Neural Networks", "Backpropagation", "Activation Functions"],
      "created_at": "2024-03-06T12:00:00Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/lectures/course/course_xyz789" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 3. Get Lecture Status
**GET** `/lectures/{lecture_id}/status`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "lecture_id": "lec_def456",
  "title": "Introduction to Neural Networks",
  "status": "completed",
  "key_concepts": ["Neural Networks", "Backpropagation"],
  "created_at": "2024-03-06T12:00:00Z",
  "processed_at": "2024-03-06T12:03:00Z"
}
```

**Status Values:**
- `pending`: Waiting for processing
- `processing`: Currently being processed
- `completed`: Processing finished
- `failed`: Processing failed

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/lectures/lec_def456/status" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 4. Process Lecture Manually
**POST** `/lectures/{lecture_id}/process`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "message": "Lecture processed successfully",
  "lecture_id": "lec_def456",
  "key_concepts": ["Neural Networks", "Backpropagation"],
  "chunks_created": 15,
  "llm_usage": {
    "model": "gpt-4",
    "tokens": 1250
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/lectures/lec_def456/process" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 📝 Tests

### 1. Generate Test
**POST** `/tests/generate`

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Query Parameters:**
- `course_id`: string (required)

**Request Body:**
```json
{
  "week_number": 1,
  "num_mcq": 5,
  "num_true_false": 3,
  "num_essay": 2,
  "difficulty": "medium"
}
```

**Response (201):**
```json
{
  "id": "test_ghi789",
  "lecture_id": "lec_def456",
  "week_number": 1,
  "questions": [
    {
      "id": "q1",
      "type": "mcq",
      "question": "What is a neural network?",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "points": 2
    }
  ],
  "total_points": 20,
  "created_at": "2024-03-06T12:00:00Z"
}
```

**Difficulty Values:**
- `easy`
- `medium`
- `hard`

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tests/generate?course_id=course_xyz789" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "week_number": 1,
    "num_mcq": 5,
    "num_true_false": 3,
    "num_essay": 2,
    "difficulty": "medium"
  }'
```

---

### 2. Get Test
**GET** `/tests/{test_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": "test_ghi789",
  "lecture_id": "lec_def456",
  "week_number": 1,
  "questions": [...],
  "total_points": 20,
  "created_at": "2024-03-06T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/tests/test_ghi789" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 3. Get Lecture Tests
**GET** `/tests/lecture/{lecture_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "total": 2,
  "tests": [
    {
      "id": "test_ghi789",
      "lecture_id": "lec_def456",
      "week_number": 1,
      "total_points": 20,
      "created_at": "2024-03-06T12:00:00Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/tests/lecture/lec_def456" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## ✅ Evaluations

### 1. Submit Test
**POST** `/evaluations/submit/{test_id}`

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "answers": [
    {
      "question_id": "q1",
      "answer": "A"
    },
    {
      "question_id": "q2",
      "answer": "True"
    },
    {
      "question_id": "q3",
      "answer": "Neural networks are computational models..."
    }
  ]
}
```

**Response (201):**
```json
{
  "attempt_id": "attempt_jkl012",
  "score": 18,
  "max_score": 20,
  "percentage": 90.0,
  "feedback": "Excellent work! Strong understanding of neural networks.",
  "question_results": [
    {
      "question_id": "q1",
      "is_correct": true,
      "points_earned": 2,
      "points_possible": 2,
      "feedback": "Correct!"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/evaluations/submit/test_ghi789" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": "q1", "answer": "A"},
      {"question_id": "q2", "answer": "True"}
    ]
  }'
```

---

### 2. Get Attempt Result
**GET** `/evaluations/attempt/{attempt_id}`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "attempt_id": "attempt_jkl012",
  "test_id": "test_ghi789",
  "score": 18,
  "max_score": 20,
  "percentage": 90.0,
  "feedback": "Excellent work!",
  "question_results": [...],
  "submitted_at": "2024-03-06T12:00:00Z"
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/evaluations/attempt/attempt_jkl012" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

### 3. Get Test Attempts
**GET** `/evaluations/test/{test_id}/attempts`

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "total": 2,
  "attempts": [
    {
      "attempt_id": "attempt_jkl012",
      "score": 18,
      "max_score": 20,
      "percentage": 90.0,
      "submitted_at": "2024-03-06T12:00:00Z"
    }
  ]
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/evaluations/test/test_ghi789/attempts" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 🔧 System Endpoints

### Health Check
**GET** `/health`

**Response (200):**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

---

### Root
**GET** `/`

**Response (200):**
```json
{
  "status": "running",
  "app": "AI Study Assistant",
  "version": "0.1.0",
  "environment": "development"
}
```

**cURL Example:**
```bash
curl -X GET "http://127.0.0.1:8000/"
```

---

## 📌 Quick Start Guide

### 1. Register and Login
```bash
# Register
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# Login and save token
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | jq -r '.access_token')

echo "Token: $TOKEN"
```

### 2. Create Course
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/courses" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"AI Course","code":"CS101","semester":"Spring 2024","instructor":"Prof. AI"}'
```

### 3. Upload Lecture
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/lectures/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "course_id=YOUR_COURSE_ID" \
  -F "week_number=1" \
  -F "title=Intro to AI" \
  -F "file=@lecture.pdf"
```

---

## 🚨 Common Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 409 Conflict
```json
{
  "detail": "Email already registered"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## 📝 Notes

1. **Authentication**: Бүх protected endpoint-үүд `Authorization: Bearer {token}` header шаарддаг
2. **File Upload**: Lecture upload зөвхөн PDF файл дэмждэг (max 10MB)
3. **Week Numbers**: 1-16 хооронд байх ёстой
4. **Test Difficulty**: `easy`, `medium`, `hard` утгууд ашиглана
5. **Question Types**: `mcq` (Multiple Choice), `true_false`, `essay`

---

## 🔗 Useful Links

- **API Documentation**: http://127.0.0.1:8000/api/docs
- **ReDoc**: http://127.0.0.1:8000/api/redoc
- **Health Check**: http://127.0.0.1:8000/health

---

**Last Updated**: 2024-03-06
**Version**: 1.0.0
