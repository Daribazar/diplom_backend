# Authentication Guide

## Overview

The authentication system uses JWT (JSON Web Tokens) for stateless authentication with bcrypt password hashing.

## Quick Start

### 1. Register a User

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "password": "securepassword123",
            "full_name": "John Doe"
        }
    )
    user = response.json()
    print(f"Registered: {user['email']}")
```

### 2. Login

```python
response = await client.post(
    "http://localhost:8000/api/v1/auth/login",
    json={
        "email": "user@example.com",
        "password": "securepassword123"
    }
)
token_data = response.json()
access_token = token_data["access_token"]
```

### 3. Access Protected Endpoints

```python
headers = {"Authorization": f"Bearer {access_token}"}
response = await client.get(
    "http://localhost:8000/api/v1/auth/me",
    headers=headers
)
user = response.json()
print(f"Authenticated as: {user['full_name']}")
```

## Protecting Your Endpoints

### Basic Protection

```python
from fastapi import APIRouter
from src.core.dependencies import CurrentUser

router = APIRouter()

@router.get("/protected")
async def protected_route(current_user: CurrentUser):
    """This endpoint requires authentication."""
    return {
        "message": f"Hello {current_user.full_name}!",
        "user_id": current_user.id,
        "email": current_user.email
    }
```

### With Database Access

```python
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import CurrentUser, get_db

@router.get("/my-data")
async def get_my_data(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Protected endpoint with database access."""
    # current_user is already authenticated
    # db is the database session
    
    # Your logic here
    return {"user_id": current_user.id}
```

### Resource Ownership Validation

```python
from src.core.exceptions import ForbiddenException

@router.get("/courses/{course_id}")
async def get_course(
    course_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Get course - only owner can access."""
    repo = CourseRepository(db)
    course = await repo.get_by_id(course_id)
    
    if not course:
        raise HTTPException(404, "Course not found")
    
    # Check ownership
    if course.owner_id != current_user.id:
        raise ForbiddenException("Not authorized to access this course")
    
    return course
```

## Security Utilities

### Password Hashing

```python
from src.core.security import get_password_hash, verify_password

# Hash a password
hashed = get_password_hash("mypassword")

# Verify a password
is_valid = verify_password("mypassword", hashed)
```

### JWT Tokens

```python
from datetime import timedelta
from src.core.security import create_access_token, decode_access_token

# Create token
token = create_access_token(
    data={"sub": "user_123"},
    expires_delta=timedelta(minutes=30)
)

# Decode token
payload = decode_access_token(token)
if payload:
    user_id = payload.get("sub")
```

## Error Handling

### Common Errors

**401 Unauthorized:**
- Invalid token
- Expired token
- Missing token
- Wrong password

**403 Forbidden:**
- Inactive user
- Insufficient permissions

**409 Conflict:**
- Email already registered

### Custom Error Responses

```python
from fastapi import HTTPException, status
from src.core.exceptions import InvalidCredentialsError

try:
    # Your auth logic
    pass
except InvalidCredentialsError as e:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(e),
        headers={"WWW-Authenticate": "Bearer"}
    )
```

## Testing

### With Swagger UI

1. Go to http://localhost:8000/api/docs
2. Click "POST /api/v1/auth/register"
3. Click "Try it out"
4. Fill in the request body
5. Click "Execute"
6. Copy the token from login response
7. Click "Authorize" button (top right)
8. Enter: `Bearer <your_token>`
9. Now you can access protected endpoints

### With Python Script

```bash
poetry run python scripts/test_auth.py
```

### With pytest

```python
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        
        # Access protected endpoint
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
```

## Configuration

### Environment Variables

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
SECRET_KEY=your-app-secret-key
```

### Settings

```python
from src.config import settings

# Access settings
print(settings.JWT_SECRET_KEY)
print(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
```

## Best Practices

### 1. Always Use HTTPS in Production

```python
# In production, enforce HTTPS
if settings.APP_ENV == "production":
    # Redirect HTTP to HTTPS
    pass
```

### 2. Use Strong Secrets

```bash
# Generate strong secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Set Appropriate Token Expiration

```python
# Short-lived tokens are more secure
ACCESS_TOKEN_EXPIRE_MINUTES=30  # 30 minutes
```

### 4. Validate User is Active

```python
# Already done in get_current_user dependency
if not user.is_active:
    raise HTTPException(403, "Inactive user")
```

### 5. Don't Leak Information in Errors

```python
# Bad: "User not found" vs "Wrong password"
# Good: "Invalid email or password" (same message)
```

## Advanced Usage

### Custom Token Claims

```python
from src.core.security import create_access_token

token = create_access_token(
    data={
        "sub": user.id,
        "email": user.email,
        "role": "admin"  # Custom claim
    }
)
```

### Multiple Authentication Schemes

```python
from fastapi.security import HTTPBasic, HTTPBearer

# Support both Bearer and Basic auth
bearer_scheme = HTTPBearer()
basic_scheme = HTTPBasic()

async def get_current_user_flexible(
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    basic: Optional[HTTPBasicCredentials] = Depends(basic_scheme)
):
    if bearer:
        # Validate JWT
        pass
    elif basic:
        # Validate username/password
        pass
    else:
        raise HTTPException(401, "Authentication required")
```

### Role-Based Access Control (Future)

```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

def require_role(required_role: UserRole):
    async def role_checker(current_user: CurrentUser):
        if current_user.role != required_role:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return role_checker

@router.get("/admin-only")
async def admin_route(
    current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))]
):
    return {"message": "Admin access granted"}
```

## Troubleshooting

### "Invalid authentication credentials"

- Check token is valid
- Check token hasn't expired
- Check Authorization header format: `Bearer <token>`

### "User not found"

- User was deleted after token was issued
- Token contains invalid user ID

### "Inactive user"

- User account was deactivated
- Check `is_active` field in database

### "Email already registered"

- Email must be unique
- Check if user already exists

## Security Checklist

- [x] Passwords hashed with bcrypt
- [x] JWT tokens with expiration
- [x] Secure token validation
- [x] Active user check
- [x] No passwords in responses
- [ ] HTTPS in production
- [ ] Rate limiting (future)
- [ ] Refresh tokens (future)
- [ ] Password reset (future)
- [ ] Email verification (future)

## Summary

The authentication system provides:
- Secure password hashing
- JWT token-based authentication
- Easy-to-use dependency injection
- Clean Architecture compliance
- Production-ready security

Use `CurrentUser` dependency to protect any endpoint!
