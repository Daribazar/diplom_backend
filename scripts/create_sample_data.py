"""Create sample data for testing."""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.4_infrastructure.database.connection import async_session_maker
from src.4_infrastructure.database.repositories.user_repository import UserRepository
from src.4_infrastructure.database.repositories.course_repository import CourseRepository
from src.4_infrastructure.database.repositories.lecture_repository import LectureRepository
from src.3_domain.entities.user import User
from src.3_domain.entities.course import Course
from src.3_domain.entities.lecture import Lecture
from src.core.security import get_password_hash


async def create_sample_data():
    """Create sample users, courses, and lectures."""
    print("Creating sample data...")
    
    async with async_session_maker() as session:
        try:
            # Create sample user
            user_repo = UserRepository(session)
            user = User(
                id="user_sample001",
                email="student@example.com",
                full_name="John Doe"
            )
            created_user = await user_repo.create(user, get_password_hash("password123"))
            print(f"✅ Created user: {created_user.email}")
            
            # Create sample course
            course_repo = CourseRepository(session)
            course = Course(
                id="course_sample001",
                name="Introduction to Machine Learning",
                code="CS401",
                semester="Fall 2024",
                owner_id=created_user.id,
                instructor="Dr. Smith"
            )
            created_course = await course_repo.create(course)
            print(f"✅ Created course: {created_course.name}")
            
            # Create sample lectures
            lecture_repo = LectureRepository(session)
            lectures_data = [
                ("Week 1: Introduction to ML", 1),
                ("Week 2: Linear Regression", 2),
                ("Week 3: Classification", 3),
            ]
            
            for title, week in lectures_data:
                lecture = Lecture(
                    id=f"lec_sample{week:03d}",
                    course_id=created_course.id,
                    week_number=week,
                    title=title,
                    status="pending"
                )
                created_lecture = await lecture_repo.create(lecture)
                print(f"✅ Created lecture: {created_lecture.title}")
            
            await session.commit()
            print("\n✅ Sample data created successfully!")
            print(f"\nTest credentials:")
            print(f"  Email: student@example.com")
            print(f"  Password: password123")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating sample data: {str(e)}")
            raise


if __name__ == "__main__":
    asyncio.run(create_sample_data())
