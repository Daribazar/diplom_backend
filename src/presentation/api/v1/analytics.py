"""Analytics API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_current_user
from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.lecture import LectureModel
from src.infrastructure.database.models.student_attempt import StudentAttemptModel
from src.infrastructure.database.models.test import TestModel
from src.infrastructure.database.models.user import UserModel
from src.presentation.api.v1.analytics_helpers import (
    DEFAULT_CHANGE_SCORE,
    DEFAULT_CHANGE_TESTS,
    DEFAULT_CHANGE_TIME,
    DEFAULT_TIME_MINUTES,
    ROLE_TEACHER,
    attempts_base_query,
    empty_overview,
    extract_topic_name,
    get_course_code_for_attempt,
    round_score,
    student_course_filter,
    with_optional_course_filter,
)
from src.presentation.schemas.analytics import (
    AnalyticsOverviewResponse,
    BloomTaxonomyData,
    CourseComparisonData,
    CoursePerformanceData,
    TopicMasteryData,
    WeeklyScoreData,
)


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall analytics overview.

    Returns:
    - Total score average
    - Total tests completed
    - Average time spent
    - Highest score
    """
    query = with_optional_course_filter(
        attempts_base_query(current_user.id),
        course_id,
    )
    result = await db.execute(query)
    attempts = result.scalars().all()

    if not attempts:
        return empty_overview()

    total_score_avg = sum(a.percentage or 0 for a in attempts) / len(attempts)
    total_tests = len(attempts)
    highest_score = max((a.percentage or 0 for a in attempts), default=0)
    highest_attempt = max(attempts, key=lambda a: a.percentage or 0, default=None)
    highest_course = await get_course_code_for_attempt(db, highest_attempt)

    return AnalyticsOverviewResponse(
        total_score_average=round_score(total_score_avg),
        total_tests=total_tests,
        average_time_minutes=DEFAULT_TIME_MINUTES,
        highest_score=round_score(highest_score),
        highest_score_course=highest_course,
        score_change=DEFAULT_CHANGE_SCORE,
        tests_change=DEFAULT_CHANGE_TESTS,
        time_change=DEFAULT_CHANGE_TIME,
    )


@router.get("/weekly-scores", response_model=list[WeeklyScoreData])
async def get_weekly_scores(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get weekly score progression.

    Returns scores grouped by week number.
    """
    # Query attempts with lecture week information
    query = (
        select(
            LectureModel.week_number,
            func.avg(StudentAttemptModel.percentage).label("avg_score"),
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
            score=round(row.avg_score, 1) if row.avg_score else 0,
        )
        for row in rows
    ]


@router.get("/bloom-taxonomy", response_model=list[BloomTaxonomyData])
async def get_bloom_taxonomy(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get Bloom's Taxonomy performance breakdown.

    Returns performance across cognitive levels.
    """
    query = with_optional_course_filter(
        attempts_base_query(current_user.id),
        course_id,
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
        "Бүтээх": [],
    }

    for attempt in attempts:
        if attempt.analytics:
            # Map difficulty to Bloom's levels
            analytics = attempt.analytics
            if "by_difficulty" in analytics:
                for diff, stats in analytics["by_difficulty"].items():
                    if stats["total"] > 0:
                        accuracy = stats["correct"] / stats["total"] * 100
                        if diff == "easy":
                            bloom_scores["Санах"].append(accuracy)
                            bloom_scores["Ойлгох"].append(accuracy)
                        elif diff == "medium":
                            bloom_scores["Хэрэглэх"].append(accuracy)
                            bloom_scores["Шинжлэх"].append(accuracy)
                        else:  # hard
                            bloom_scores["Үнэлэх"].append(accuracy)
                            bloom_scores["Бүтээх"].append(accuracy)

    return [
        BloomTaxonomyData(
            category=category,
            score=round_score(sum(scores) / len(scores)) if scores else 0,
        )
        for category, scores in bloom_scores.items()
    ]


@router.get("/topic-mastery", response_model=list[TopicMasteryData])
async def get_topic_mastery(
    course_id: Optional[str] = Query(None, description="Filter by course ID"),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
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
            func.avg(StudentAttemptModel.percentage).label("avg_score"),
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
            topic_name = extract_topic_name(row.title, row.key_concepts)

        score = round(row.avg_score, 1) if row.avg_score else 0
        topic_data.append(
            TopicMasteryData(topic=topic_name[:30], mastery=score)  # Limit length
        )

    return topic_data[:10]  # Return top 10 topics


@router.get("/course-comparison", response_model=list[CourseComparisonData])
async def get_course_comparison(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get performance comparison across all courses.

    Returns average score for each course.
    """
    query = (
        select(
            CourseModel.id,
            CourseModel.name,
            CourseModel.code,
            func.avg(StudentAttemptModel.percentage).label("avg_score"),
            func.count(StudentAttemptModel.id).label("test_count"),
        )
        .join(LectureModel, LectureModel.course_id == CourseModel.id)
        .join(TestModel, TestModel.lecture_id == LectureModel.id)
        .join(StudentAttemptModel, StudentAttemptModel.test_id == TestModel.id)
        .where(
            and_(
                CourseModel.owner_id == current_user.id,
                StudentAttemptModel.student_id == current_user.id,
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
            average_score=round_score(row.avg_score),
            test_count=row.test_count,
        )
        for row in rows
    ]


@router.get("/course-performance", response_model=list[CoursePerformanceData])
async def get_course_performance(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed performance data for all courses.

    Returns comprehensive stats for each course.
    """
    course_filter = (
        CourseModel.owner_id == current_user.id
        if current_user.role == ROLE_TEACHER
        else student_course_filter(current_user.id)
    )
    courses_result = await db.execute(select(CourseModel).where(course_filter))
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
                    StudentAttemptModel.student_id == current_user.id,
                )
            )
        )
        attempts = attempts_result.scalars().all()

        avg_score = (
            sum(a.percentage or 0 for a in attempts) / len(attempts) if attempts else 0
        )

        performance_data.append(
            CoursePerformanceData(
                course_id=course.id,
                course_name=course.name,
                course_code=course.code,
                instructor=course.instructor or "N/A",
                average_score=round_score(avg_score),
                tests_completed=len(attempts),
                lectures_uploaded=lectures_count,
                color="blue",  # Default color, can be enhanced
            )
        )

    return performance_data
