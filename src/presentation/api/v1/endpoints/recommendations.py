"""Recommendation endpoints."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from collections import defaultdict

from src.core.dependencies import get_db, CurrentUser
from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.lecture import LectureModel
from src.infrastructure.database.models.test import TestModel
from src.infrastructure.database.models.student_attempt import StudentAttemptModel
from src.core.exceptions import NotFoundError

router = APIRouter()


@router.get(
    "/course/{course_id}",
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
    
    # Verify course exists and user has access
    result = await db.execute(
        select(CourseModel).where(
            CourseModel.id == course_id,
            CourseModel.owner_id == current_user.id
        )
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Get all lectures for this course
    lectures_result = await db.execute(
        select(LectureModel)
        .where(LectureModel.course_id == course_id)
        .order_by(LectureModel.week_number)
    )
    lectures = lectures_result.scalars().all()
    
    if not lectures:
        return {
            "course_id": course_id,
            "based_on_week": 0,
            "focus_areas": [],
            "study_plan": [],
            "ai_advice": "Хичээлийн материал оруулж, тест өгснөөр хувийн зөвлөмж авах боломжтой болно."
        }
    
    # Get all tests and attempts for this course
    lecture_ids = [l.id for l in lectures]
    tests_result = await db.execute(
        select(TestModel).where(TestModel.lecture_id.in_(lecture_ids))
    )
    tests = tests_result.scalars().all()
    
    if not tests:
        return {
            "course_id": course_id,
            "based_on_week": lectures[-1].week_number if lectures else 0,
            "focus_areas": [],
            "study_plan": [],
            "ai_advice": "Тест үүсгэж, өгснөөр таны хувийн зөвлөмж бэлтгэгдэх болно."
        }
    
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
        return {
            "course_id": course_id,
            "based_on_week": lectures[-1].week_number if lectures else 0,
            "focus_areas": [],
            "study_plan": [],
            "ai_advice": "Тест өгснөөр таны хувийн зөвлөмж автоматаар үүснэ."
        }
    
    # Analyze weak topics from attempts
    weak_topics = defaultdict(lambda: {"total": 0, "wrong": 0, "percentage": 0})
    
    for attempt in attempts:
        if attempt.weak_topics:
            for topic in attempt.weak_topics:
                if isinstance(topic, dict):
                    topic_name = topic.get("topic", "Unknown")
                    weak_topics[topic_name]["total"] += 1
                    weak_topics[topic_name]["wrong"] += 1
                elif isinstance(topic, str):
                    weak_topics[topic]["total"] += 1
                    weak_topics[topic]["wrong"] += 1
    
    # Calculate percentages and sort by weakness
    focus_areas = []
    for topic, stats in weak_topics.items():
        if stats["total"] > 0:
            # Lower percentage = weaker topic
            percentage = max(0, 100 - (stats["wrong"] / stats["total"] * 100))
            priority = "high" if percentage < 50 else "medium" if percentage < 75 else "low"
            focus_areas.append({
                "topic": topic,
                "percentage": round(percentage),
                "priority": priority
            })
    
    # Sort by percentage (weakest first)
    focus_areas.sort(key=lambda x: x["percentage"])
    focus_areas = focus_areas[:5]  # Top 5 weak areas
    
    # Generate study plan
    study_plan = []
    
    if focus_areas:
        # Day 1: Review weak topics
        day1_tasks = []
        for i, area in enumerate(focus_areas[:3]):
            day1_tasks.append({
                "duration": 30,
                "description": f"{area['topic']} сэдвийн материал дахин унших"
            })
        study_plan.append({
            "day": 1,
            "title": "Сул талуудыг дахин судлах",
            "tasks": day1_tasks
        })
        
        # Day 2: Practice exercises
        day2_tasks = []
        for area in focus_areas[:3]:
            day2_tasks.append({
                "duration": 25,
                "description": f"{area['topic']}-тай холбоотой дасгал бодох"
            })
        study_plan.append({
            "day": 2,
            "title": "Дасгал хийх",
            "tasks": day2_tasks
        })
        
        # Day 3: Take practice test
        study_plan.append({
            "day": 3,
            "title": "Дасгал тест өгөх",
            "tasks": [
                {
                    "duration": 45,
                    "description": "Сул сэдвүүдээр дасгал тест өгөх"
                },
                {
                    "duration": 15,
                    "description": "Үр дүнгээ шинжлэх, алдаагаа засах"
                }
            ]
        })
    
    # Generate AI advice
    latest_attempt = attempts[0]
    avg_score = latest_attempt.percentage or 0
    
    if avg_score >= 80:
        ai_advice = f"Сайн ахиц гаргаж байна! Одоогийн түвшингээ хадгалахын тулд тогтмол давтлага хийж, илүү төвөгтэй асуултууд бодож үзээрэй."
    elif avg_score >= 60:
        ai_advice = f"Ахиц гарч байна. {focus_areas[0]['topic'] if focus_areas else 'Сул сэдвүүд'}-д илүү анхаарч, өдөр бүр 30-45 минут зарцуулбал үр дүн сайжирна."
    else:
        ai_advice = f"Суурь ойлголтоо бэхжүүлэх шаардлагатай байна. {focus_areas[0]['topic'] if focus_areas else 'Үндсэн сэдвүүд'}-ээс эхлээд, өдөр бүр 1 цаг зарцуулж судлаарай."
    
    # Get the most recent week number
    latest_week = lectures[-1].week_number if lectures else 0
    
    return {
        "course_id": course_id,
        "based_on_week": latest_week,
        "focus_areas": focus_areas,
        "study_plan": study_plan,
        "ai_advice": ai_advice
    }
