"""Dashboard API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.core.dependencies import get_db, get_current_user
from src.infrastructure.database.models.user import UserModel
from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.lecture import LectureModel
from src.infrastructure.database.models.test import TestModel
from src.infrastructure.database.models.student_attempt import StudentAttemptModel
from src.presentation.schemas.dashboard import DashboardStatsResponse, DashboardCourseData


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard statistics.
    
    Returns:
    - Total courses (teacher: owned, student: enrolled)
    - Total lectures uploaded
    - Total tests taken
    - Average score
    """
    from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
    
    if current_user.role == "teacher":
        # Get total courses owned by teacher
        courses_result = await db.execute(
            select(func.count(CourseModel.id)).where(
                CourseModel.owner_id == current_user.id
            )
        )
        total_courses = courses_result.scalar() or 0
        
        # Get total lectures (completed) in teacher's courses
        lectures_result = await db.execute(
            select(func.count(LectureModel.id))
            .join(CourseModel)
            .where(
                and_(
                    CourseModel.owner_id == current_user.id,
                    LectureModel.status == 'completed'
                )
            )
        )
        total_lectures = lectures_result.scalar() or 0
    else:
        # Get total enrolled courses for student
        courses_result = await db.execute(
            select(func.count(CourseEnrollmentModel.id)).where(
                and_(
                    CourseEnrollmentModel.student_id == current_user.id,
                    CourseEnrollmentModel.status == 'approved'
                )
            )
        )
        total_courses = courses_result.scalar() or 0
        
        # Get total lectures in enrolled courses
        lectures_result = await db.execute(
            select(func.count(LectureModel.id))
            .join(CourseModel)
            .join(CourseEnrollmentModel, CourseModel.id == CourseEnrollmentModel.course_id)
            .where(
                and_(
                    CourseEnrollmentModel.student_id == current_user.id,
                    CourseEnrollmentModel.status == 'approved',
                    LectureModel.status == 'completed'
                )
            )
        )
        total_lectures = lectures_result.scalar() or 0
    
    # Get test statistics
    attempts_result = await db.execute(
        select(
            func.count(StudentAttemptModel.id).label('total_tests'),
            func.avg(StudentAttemptModel.percentage).label('avg_score')
        )
        .where(StudentAttemptModel.student_id == current_user.id)
    )
    test_stats = attempts_result.first()
    
    total_tests = test_stats.total_tests if test_stats else 0
    avg_score = round(test_stats.avg_score, 1) if test_stats and test_stats.avg_score else 0
    
    return DashboardStatsResponse(
        total_courses=total_courses,
        total_lectures=total_lectures,
        total_tests=total_tests,
        average_score=avg_score
    )


@router.get("/courses", response_model=list[DashboardCourseData])
async def get_dashboard_courses(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get courses with their statistics for dashboard.
    
    Returns courses with:
    - Lecture count
    - Test count
    - Average score
    
    Teacher: owned courses
    Student: enrolled courses
    """
    from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
    
    if current_user.role == "teacher":
        # Get teacher's courses
        courses_result = await db.execute(
            select(CourseModel).where(CourseModel.owner_id == current_user.id)
        )
        courses = courses_result.scalars().all()
    else:
        # Get student's enrolled courses
        courses_result = await db.execute(
            select(CourseModel)
            .join(CourseEnrollmentModel, CourseModel.id == CourseEnrollmentModel.course_id)
            .where(
                and_(
                    CourseEnrollmentModel.student_id == current_user.id,
                    CourseEnrollmentModel.status == 'approved'
                )
            )
        )
        courses = courses_result.scalars().all()
    
    course_data = []
    
    for course in courses:
        # Get lectures count
        lectures_result = await db.execute(
            select(func.count(LectureModel.id)).where(
                and_(
                    LectureModel.course_id == course.id,
                    LectureModel.status == 'completed'
                )
            )
        )
        lectures_count = lectures_result.scalar() or 0
        
        # Get test statistics for this course
        attempts_result = await db.execute(
            select(
                func.count(StudentAttemptModel.id).label('test_count'),
                func.avg(StudentAttemptModel.percentage).label('avg_score')
            )
            .join(TestModel)
            .join(LectureModel)
            .where(
                and_(
                    LectureModel.course_id == course.id,
                    StudentAttemptModel.student_id == current_user.id
                )
            )
        )
        test_stats = attempts_result.first()
        
        tests_count = test_stats.test_count if test_stats else 0
        avg_score = round(test_stats.avg_score, 1) if test_stats and test_stats.avg_score else 0
        
        course_data.append(DashboardCourseData(
            id=course.id,
            name=course.name,
            code=course.code,
            semester=course.semester,
            instructor=course.instructor or "",
            color=course.color or "blue",
            lectures_uploaded=lectures_count,
            tests_completed=tests_count,
            average_score=avg_score
        ))
    
    return course_data
