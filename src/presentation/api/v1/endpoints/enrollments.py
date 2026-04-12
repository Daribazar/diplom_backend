"""Enrollment API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import uuid

from src.core.dependencies import get_db, get_current_user
from src.infrastructure.database.models.user import UserModel
from src.infrastructure.database.models.course import CourseModel
from src.infrastructure.database.models.enrollment import CourseEnrollmentModel
from src.presentation.schemas.enrollment import (
    EnrollmentRequest,
    EnrollmentResponse,
    EnrollmentApprovalRequest,
    EnrollmentListResponse,
    CourseWithEnrollmentStatus
)


router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post("/request", response_model=EnrollmentResponse, status_code=201)
async def request_enrollment(
    request: EnrollmentRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Student requests to enroll in a course.
    """
    # Check if course exists
    course_result = await db.execute(
        select(CourseModel).where(CourseModel.id == request.course_id)
    )
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if already enrolled or requested
    existing_result = await db.execute(
        select(CourseEnrollmentModel).where(
            and_(
                CourseEnrollmentModel.course_id == request.course_id,
                CourseEnrollmentModel.student_id == current_user.id
            )
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Already {existing.status}. Cannot request again."
        )
    
    # Create enrollment request
    enrollment = CourseEnrollmentModel(
        id=f"enroll_{uuid.uuid4().hex[:12]}",
        course_id=request.course_id,
        student_id=current_user.id,
        status="pending"
    )
    
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    
    return EnrollmentResponse(
        id=enrollment.id,
        course_id=enrollment.course_id,
        student_id=enrollment.student_id,
        student_name=current_user.full_name,
        student_email=current_user.email,
        status=enrollment.status,
        requested_at=enrollment.requested_at,
        approved_at=enrollment.approved_at
    )


@router.get("/course/{course_id}", response_model=EnrollmentListResponse)
async def get_course_enrollments(
    course_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all enrollment requests for a course (teacher only).
    """
    # Check if user is the course owner (teacher)
    course_result = await db.execute(
        select(CourseModel).where(CourseModel.id == course_id)
    )
    course = course_result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    if course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only course teacher can view enrollments")
    
    # Get all enrollments
    enrollments_result = await db.execute(
        select(CourseEnrollmentModel, UserModel)
        .join(UserModel, CourseEnrollmentModel.student_id == UserModel.id)
        .where(CourseEnrollmentModel.course_id == course_id)
        .order_by(CourseEnrollmentModel.requested_at.desc())
    )
    enrollments = enrollments_result.all()
    
    enrollment_list = [
        EnrollmentResponse(
            id=enrollment.id,
            course_id=enrollment.course_id,
            student_id=enrollment.student_id,
            student_name=student.full_name,
            student_email=student.email,
            status=enrollment.status,
            requested_at=enrollment.requested_at,
            approved_at=enrollment.approved_at
        )
        for enrollment, student in enrollments
    ]
    
    return EnrollmentListResponse(
        total=len(enrollment_list),
        enrollments=enrollment_list
    )


@router.post("/approve")
async def approve_enrollment(
    request: EnrollmentApprovalRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Teacher approves or rejects enrollment request.
    """
    # Get enrollment
    enrollment_result = await db.execute(
        select(CourseEnrollmentModel).where(
            CourseEnrollmentModel.id == request.enrollment_id
        )
    )
    enrollment = enrollment_result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    
    # Check if user is the course owner
    course_result = await db.execute(
        select(CourseModel).where(CourseModel.id == enrollment.course_id)
    )
    course = course_result.scalar_one_or_none()
    if not course or course.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only course teacher can approve enrollments")
    
    # Update status
    from datetime import datetime
    enrollment.status = "approved" if request.approve else "rejected"
    if request.approve:
        enrollment.approved_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "message": f"Enrollment {'approved' if request.approve else 'rejected'} successfully",
        "enrollment_id": enrollment.id,
        "status": enrollment.status
    }


@router.get("/my-enrollments", response_model=EnrollmentListResponse)
async def get_my_enrollments(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's enrollment requests.
    """
    enrollments_result = await db.execute(
        select(CourseEnrollmentModel)
        .where(CourseEnrollmentModel.student_id == current_user.id)
        .order_by(CourseEnrollmentModel.requested_at.desc())
    )
    enrollments = enrollments_result.scalars().all()
    
    enrollment_list = [
        EnrollmentResponse(
            id=enrollment.id,
            course_id=enrollment.course_id,
            student_id=enrollment.student_id,
            student_name=current_user.full_name,
            student_email=current_user.email,
            status=enrollment.status,
            requested_at=enrollment.requested_at,
            approved_at=enrollment.approved_at
        )
        for enrollment in enrollments
    ]
    
    return EnrollmentListResponse(
        total=len(enrollment_list),
        enrollments=enrollment_list
    )


@router.get("/browse-courses", response_model=list[CourseWithEnrollmentStatus])
async def browse_all_courses(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Browse all available courses with enrollment status (for students).
    """
    # Get all courses
    courses_result = await db.execute(select(CourseModel))
    courses = courses_result.scalars().all()
    
    # Get user's enrollments
    enrollments_result = await db.execute(
        select(CourseEnrollmentModel).where(
            CourseEnrollmentModel.student_id == current_user.id
        )
    )
    enrollments = enrollments_result.scalars().all()
    enrollment_map = {e.course_id: e for e in enrollments}
    
    course_list = []
    for course in courses:
        enrollment = enrollment_map.get(course.id)
        course_list.append(CourseWithEnrollmentStatus(
            id=course.id,
            name=course.name,
            code=course.code,
            semester=course.semester,
            instructor=course.instructor or "N/A",
            color=course.color or "blue",
            enrollment_status=enrollment.status if enrollment else None,
            is_enrolled=enrollment.status == "approved" if enrollment else False
        ))
    
    return course_list
