"""Recommendation endpoints."""
from typing                     import Annotated
from fastapi                    import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio     import AsyncSession
from sqlalchemy                 import select
from collections                import defaultdict

from src.core.dependencies                                  import get_db, CurrentUser
from src.infrastructure.database.models.course              import CourseModel
from src.infrastructure.database.models.lecture             import LectureModel
from src.infrastructure.database.models.test                import TestModel
from src.infrastructure.database.models.student_attempt     import StudentAttemptModel
from src.presentation.api.course_access                     import has_course_access
from src.infrastructure.database.repositories.course_repository import CourseRepository
from src.presentation.schemas.recommendation                import (
    CourseRecommendationResponse,
    FocusArea,
    StudyPlanDay,
    StudyTask,
)

router = APIRouter()


def _empty_recommendation(course_id: str, based_on_week: int, ai_advice: str) -> CourseRecommendationResponse:
    return CourseRecommendationResponse(
        course_id=course_id,
        based_on_week=based_on_week,
        focus_areas=[],
        study_plan=[],
        ai_advice=ai_advice,
    )


def _build_focus_areas(attempts: list[StudentAttemptModel]) -> list[FocusArea]:
    weak_topics = defaultdict(lambda: {"count": 0})
    for attempt in attempts:
        if not attempt.weak_topics:
            continue
        for topic in attempt.weak_topics:
            if isinstance(topic, dict):
                topic_name = topic.get("topic", "Unknown")
            elif isinstance(topic, str):
                topic_name = topic
            else:
                continue
            weak_topics[topic_name]["count"] += 1

    focus_areas: list[FocusArea] = []
    total_attempts = max(len(attempts), 1)
    for topic, stats in weak_topics.items():
        count = stats["count"]
        if count <= 0:
            continue

        # weak_topics contains topics where student underperformed in each attempt.
        # More appearances across attempts => lower mastery.
        weakness_ratio = count / total_attempts
        percentage = max(0, round(100 - weakness_ratio * 100))
        priority = "high" if weakness_ratio >= 0.7 else "medium" if weakness_ratio >= 0.4 else "low"
        focus_areas.append(FocusArea(topic=topic, percentage=round(percentage), priority=priority))

    focus_areas.sort(key=lambda x: (x.percentage, x.topic))
    return focus_areas[:5]


def _build_study_plan(focus_areas: list[FocusArea]) -> list[StudyPlanDay]:
    if not focus_areas:
        return []

    day1_tasks = [StudyTask(duration=30, description=f"{area.topic} сэдвийн материал дахин унших") for area in focus_areas[:3]]
    day2_tasks = [StudyTask(duration=25, description=f"{area.topic}-тай холбоотой дасгал бодох") for area in focus_areas[:3]]

    return [
        StudyPlanDay(day=1, title="Сул талуудыг дахин судлах", tasks=day1_tasks),
        StudyPlanDay(day=2, title="Дасгал хийх", tasks=day2_tasks),
        StudyPlanDay(
            day=3,
            title="Дасгал тест өгөх",
            tasks=[
                StudyTask(duration=45, description="Сул сэдвүүдээр дасгал тест өгөх"),
                StudyTask(duration=15, description="Үр дүнгээ шинжлэх, алдаагаа засах"),
            ],
        ),
    ]


def _build_ai_advice(avg_score: float, focus_areas: list[FocusArea]) -> str:
    primary_topic = focus_areas[0].topic if focus_areas else "Үндсэн сэдвүүд"
    if avg_score >= 80:
        return "Сайн ахиц гаргаж байна! Одоогийн түвшингээ хадгалахын тулд тогтмол давтлага хийж, илүү төвөгтэй асуултууд бодож үзээрэй."
    if avg_score >= 60:
        return f"Ахиц гарч байна. {primary_topic}-д илүү анхаарч, өдөр бүр 30-45 минут зарцуулбал үр дүн сайжирна."
    return f"Суурь ойлголтоо бэхжүүлэх шаардлагатай байна. {primary_topic}-ээс эхлээд, өдөр бүр 1 цаг зарцуулж судлаарай."


@router.get(
    "/course/{course_id}",
    response_model=CourseRecommendationResponse,
    summary="Get personalized recommendations",
    description="Get AI-powered study recommendations based on test performance"
)
async def get_course_recommendations(
    course_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Generate personalized study recommendations based on:
    - Recent test performance
    - Weak topics identified from wrong answers
    - Study patterns and progress
    """
    
    # Verify course exists and user has access (owner or approved enrolled student)
    result = await db.execute(select(CourseModel).where(CourseModel.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    course_repo = CourseRepository(db)
    can_access = await has_course_access(db, course_repo, course_id, current_user.id, current_user.role)
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this course"
        )
    
    # Get all lectures for this course
    lectures_result = await db.execute(
        select(LectureModel)
        .where(LectureModel.course_id == course_id)
        .order_by(LectureModel.week_number)
    )
    lectures = lectures_result.scalars().all()
    
    if not lectures:
        return _empty_recommendation(
            course_id=course_id,
            based_on_week=0,
            ai_advice="Хичээлийн материал оруулж, тест өгснөөр хувийн зөвлөмж авах боломжтой болно.",
        )
    
    # Get all tests and attempts for this course
    lecture_ids = [l.id for l in lectures]
    tests_result = await db.execute(
        select(TestModel).where(TestModel.lecture_id.in_(lecture_ids))
    )
    tests = tests_result.scalars().all()
    
    if not tests:
        return _empty_recommendation(
            course_id=course_id,
            based_on_week=lectures[-1].week_number if lectures else 0,
            ai_advice="Тест үүсгэж, өгснөөр таны хувийн зөвлөмж бэлтгэгдэх болно.",
        )
    
    test_ids = [t.id for t in tests]
    attempts_result = await db.execute(
        select(StudentAttemptModel)
        .where(
            StudentAttemptModel.test_id.in_(test_ids),
            StudentAttemptModel.student_id == current_user.id
        )
        .order_by(StudentAttemptModel.created_at.desc())
    )
    attempts = attempts_result.scalars().all()
    
    if not attempts:
        return _empty_recommendation(
            course_id=course_id,
            based_on_week=lectures[-1].week_number if lectures else 0,
            ai_advice="Тест өгснөөр таны хувийн зөвлөмж автоматаар үүснэ.",
        )

    focus_areas = _build_focus_areas(attempts)
    study_plan = _build_study_plan(focus_areas)

    latest_attempt = attempts[0]
    avg_score = latest_attempt.percentage or 0
    ai_advice = _build_ai_advice(avg_score, focus_areas)
    
    # Get the most recent week number
    latest_week = lectures[-1].week_number if lectures else 0
    
    return CourseRecommendationResponse(
        course_id=course_id,
        based_on_week=latest_week,
        focus_areas=focus_areas,
        study_plan=study_plan,
        ai_advice=ai_advice,
    )
