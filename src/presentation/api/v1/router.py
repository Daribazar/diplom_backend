"""Main API v1 router."""
from fastapi import APIRouter
from src.presentation.api.v1.endpoints import auth, courses, lectures, tests, evaluations

api_router = APIRouter(prefix="/api/v1")

# Include routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(lectures.router, prefix="/lectures", tags=["Lectures"])
api_router.include_router(tests.router, prefix="/tests", tags=["Tests"])
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["Evaluations"])
