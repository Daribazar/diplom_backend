"""Analytics API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from src.core.dependencies import get_db, get_current_user
from src.infrastructure.database.models.user import UserModel
from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.lecture import LectureModel
from src.infrastructure.database.models.test import TestModel
from src.infrastructure.database.models.student_attempt import StudentAttemptModel
from src.presentation.schemas.analytics import (
    AnalyticsOverviewResponse,
    WeeklyScoreData,
    BloomTaxonomyData,
    TopicMasteryData,
    CoursePerformanceData,
    CourseComparisonData
)


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall analytics overview.
    
    Returns:
    - Total score average
    - Total tests completed
    - Average time spent
    - Highest score
    """
    # Base query for user's attempts
    query = select(StudentAttemptModel).where(
        StudentAttemptModel.student_id == current_user.id
    )
    
    # Filter by course if specified
    if course_id:
        query = query.join(TestModel).join(LectureModel).where(
            LectureModel.course_id == course_id
        )
    
    result = await db.execute(query)
    attempts = result.scalars().all()
    
    if not attempts:
        return AnalyticsOverviewResponse(
            total_score_average=0,
            total_tests=0,
            average_time_minutes=0,
            highest_score=0,
            highest_score_course=None,
            score_change=0,
            tests_change=0,
            time_change=0
        )
    
    # Calculate statistics
    total_score_avg = sum(a.percentage or 0 for a in attempts) / len(attempts)
    total_tests = len(attempts)
    highest_score = max((a.percentage or 0 for a in attempts), default=0)
    
    # Find course with highest score
    highest_attempt = max(attempts, key=lambda a: a.percentage or 0, default=None)
    highest_course = None
    if highest_attempt:
        test_result = await db.execute(
            select(TestModel).where(TestModel.id == highest_attempt.test_id)
        )
        test = test_result.scalar_one_or_none()
        if test:
            lecture_result = await db.execute(
                select(LectureModel).where(LectureModel.id == test.lecture_id)
            )
            lecture = lecture_result.scalar_one_or_none()
            if lecture:
                course_result = await db.execute(
                    select(CourseModel).where(CourseModel.id == lecture.course_id)
                )
                course = course_result.scalar_one_or_none()
                if course:
                    highest_course = course.code
    
    # Calculate average time (mock for now, can be enhanced)
    average_time = 21  # Default mock value
    
    return AnalyticsOverviewResponse(
        total_score_average=round(total_score_avg, 1),
        total_tests=total_tests,
        average_time_minutes=average_time,
        highest_score=round(highest_score, 1),
        highest_score_course=highest_course,
        score_change=3.2,  # Mock change data
        tests_change=2,
        time_change=-2
    )


@router.get("/weekly-scores", response_model=list[WeeklyScoreData])
async def get_weekly_scores(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get weekly score progression.
    
    Returns scores grouped by week number.
    """
    # Query attempts with lecture week information
    query = (
        select(
            LectureModel.week_number,
            func.avg(StudentAttemptModel.percentage).label('avg_score')
        )
        .join(TestModel, TestModel.lecture_id == LectureModel.id)
        .join(StudentAttemptModel, StudentAttemptModel.test_id == TestModel.id)
        .where(StudentAttemptModel.student_id == current_user.id)
        .group_by(LectureModel.week_number)
        .order_by(LectureModel.week_number)
    )
    
    if course_id:
        query = query.where(LectureModel.course_id == course_id)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        WeeklyScoreData(
            week=f"Week {row.week_number}",
            score=round(row.avg_score, 1) if row.avg_score else 0
        )
        for row in rows
    ]


@router.get("/bloom-taxonomy", response_model=list[BloomTaxonomyData])
async def get_bloom_taxonomy(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Bloom's Taxonomy performance breakdown.
    
    Returns performance across cognitive levels.
    """
    # Query attempts and analyze by difficulty/type
    query = select(StudentAttemptModel).where(
        StudentAttemptModel.student_id == current_user.id
    )
    
    if course_id:
        query = query.join(TestModel).join(LectureModel).where(
            LectureModel.course_id == course_id
        )
    
    result = await db.execute(query)
    attempts = result.scalars().all()
    
    # Analyze by Bloom's levels (simplified mapping)
    bloom_scores = {
        "Санах": [],
        "Ойлгох": [],
        "Хэрэглэх": [],
        "Шинжлэх": [],
        "Үнэлэх": [],
        "Бүтээх": []
    }
    
    for attempt in attempts:
        if attempt.analytics:
            # Map difficulty to Bloom's levels
            analytics = attempt.analytics
            if 'by_difficulty' in analytics:
                for diff, stats in analytics['by_difficulty'].items():
                    if stats['total'] > 0:
                        accuracy = stats['correct'] / stats['total'] * 100
                        if diff == 'easy':
                            bloom_scores["Санах"].append(accuracy)
                            bloom_scores["Ойлгох"].append(accuracy)
                        elif diff == 'medium':
                            bloom_scores["Хэрэглэх"].append(accuracy)
                            bloom_scores["Шинжлэх"].append(accuracy)
                        else:  # hard
                            bloom_scores["Үнэлэх"].append(accuracy)
                            bloom_scores["Бүтээх"].append(accuracy)
    
    return [
        BloomTaxonomyData(
            category=category,
            score=round(sum(scores) / len(scores), 1) if scores else 0
        )
        for category, scores in bloom_scores.items()
    ]


@router.get("/topic-mastery", response_model=list[TopicMasteryData])
async def get_topic_mastery(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get topic mastery breakdown.
    
    Returns mastery level for each topic.
    """
    # Query lectures and their test performance
    query = (
        select(
            LectureModel.title,
            LectureModel.key_concepts,
            func.avg(StudentAttemptModel.percentage).label('avg_score')
        )
        .join(TestModel, TestModel.lecture_id == LectureModel.id)
        .join(StudentAttemptModel, StudentAttemptModel.test_id == TestModel.id)
        .where(StudentAttemptModel.student_id == current_user.id)
        .group_by(LectureModel.id, LectureModel.title, LectureModel.key_concepts)
    )
    
    if course_id:
        query = query.where(LectureModel.course_id == course_id)
    
    result = await db.execute(query)
    rows = result.all()
    
    topic_data = []
    for row in rows:
        # Extract first key concept as topic name
        topic_name = row.title
        if row.key_concepts and len(row.key_concepts) > 0:
            topic_name = row.key_concepts[0] if isinstance(row.key_concepts, list) else row.title
        
        score = round(row.avg_score, 1) if row.avg_score else 0
        topic_data.append(TopicMasteryData(
            topic=topic_name[:30],  # Limit length
            mastery=score
        ))
    
    return topic_data[:10]  # Return top 10 topics


@router.get("/course-comparison", response_model=list[CourseComparisonData])
async def get_course_comparison(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance comparison across all courses.
    
    Returns average score for each course.
    """
    # Query all user's courses with their performance
    query = (
        select(
            CourseModel.id,
            CourseModel.name,
            CourseModel.code,
            func.avg(StudentAttemptModel.percentage).label('avg_score'),
            func.count(StudentAttemptModel.id).label('test_count')
        )
        .join(LectureModel, LectureModel.course_id == CourseModel.id)
        .join(TestModel, TestModel.lecture_id == LectureModel.id)
        .join(StudentAttemptModel, StudentAttemptModel.test_id == TestModel.id)
        .where(
            and_(
                CourseModel.owner_id == current_user.id,
                StudentAttemptModel.student_id == current_user.id
            )
        )
        .group_by(CourseModel.id, CourseModel.name, CourseModel.code)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        CourseComparisonData(
            course_code=row.code,
            course_name=row.name,
            average_score=round(row.avg_score, 1) if row.avg_score else 0,
            test_count=row.test_count
        )
        for row in rows
    ]


@router.get("/course-performance", response_model=list[CoursePerformanceData])
async def get_course_performance(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed performance data for all courses.
    
    Returns comprehensive stats for each course.
    """
    # Query user's courses
    courses_result = await db.execute(
        select(CourseModel).where(CourseModel.owner_id == current_user.id)
    )
    courses = courses_result.scalars().all()
    
    performance_data = []
    
    for course in courses:
        # Get lectures count
        lectures_result = await db.execute(
            select(func.count(LectureModel.id)).where(
                LectureModel.course_id == course.id
            )
        )
        lectures_count = lectures_result.scalar() or 0
        
        # Get tests and attempts
        attempts_result = await db.execute(
            select(StudentAttemptModel)
            .join(TestModel)
            .join(LectureModel)
            .where(
                and_(
                    LectureModel.course_id == course.id,
                    StudentAttemptModel.student_id == current_user.id
                )
            )
        )
        attempts = attempts_result.scalars().all()
        
        avg_score = 0
        if attempts:
            avg_score = sum(a.percentage or 0 for a in attempts) / len(attempts)
        
        performance_data.append(CoursePerformanceData(
            course_id=course.id,
            course_name=course.name,
            course_code=course.code,
            instructor=course.instructor or "N/A",
            average_score=round(avg_score, 1),
            tests_completed=len(attempts),
            lectures_uploaded=lectures_count,
            color="blue"  # Default color, can be enhanced
        ))
    
    return performance_data
