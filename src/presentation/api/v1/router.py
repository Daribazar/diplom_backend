"""Main API v1 router."""

from fastapi import APIRouter
from src.presentation.api.v1.endpoints import (
    auth,
    courses,
    lectures,
    tests,
    evaluations,
    recommendations,
    dashboard,
    enrollments,
)
from src.presentation.api.v1 import analytics

api_router = APIRouter(prefix="/api/v1")

# Include routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, tags=["Dashboard"])
api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
api_router.include_router(lectures.router, prefix="/lectures", tags=["Lectures"])
api_router.include_router(tests.router, prefix="/tests", tags=["Tests"])
api_router.include_router(
    evaluations.router, prefix="/evaluations", tags=["Evaluations"]
)
api_router.include_router(
    recommendations.router, prefix="/recommendations", tags=["Recommendations"]
)
api_router.include_router(analytics.router, tags=["Analytics"])
api_router.include_router(enrollments.router, tags=["Enrollments"])
