"""Test the test generation functionality."""
import asyncio
import httpx
import json


BASE_URL = "http://localhost:8000/api/v1"


async def test_test_generation():
    """Test test generation workflow."""
    print("=" * 60)
    print("TEST GENERATION WORKFLOW TEST")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Step 1: Register/Login
        print("\n1. Logging in...")
        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )
        
        if login_response.status_code != 200:
            print("❌ Login failed. Please register first:")
            print("   python scripts/test_auth.py")
            return
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in successfully")
        
        # Step 2: Get courses
        print("\n2. Getting courses...")
        courses_response = await client.get(
            f"{BASE_URL}/courses",
            headers=headers
        )
        
        if courses_response.status_code != 200 or not courses_response.json()["courses"]:
            print("❌ No courses found. Please create a course first:")
            print("   python scripts/test_courses.py")
            return
        
        course = courses_response.json()["courses"][0]
        course_id = course["id"]
        print(f"✅ Found course: {course['title']} ({course_id})")
        
        # Step 3: Get lectures
        print("\n3. Getting lectures...")
        lectures_response = await client.get(
            f"{BASE_URL}/lectures/course/{course_id}",
            headers=headers
        )
        
        if lectures_response.status_code != 200:
            print("❌ Failed to get lectures")
            return
        
        lectures = lectures_response.json()["lectures"]
        
        if not lectures:
            print("❌ No lectures found. Please upload a lecture first")
            return
        
        # Find a completed lecture
        completed_lecture = None
        for lecture in lectures:
            if lecture["status"] == "completed":
                completed_lecture = lecture
                break
        
        if not completed_lecture:
            print("❌ No completed lectures found. Please wait for processing to complete")
            print("   Check status: GET /api/v1/lectures/{lecture_id}/status")
            return
        
        week_number = completed_lecture["week_number"]
        print(f"✅ Found completed lecture: Week {week_number} - {completed_lecture['title']}")
        print(f"   Key concepts: {completed_lecture.get('key_concepts', [])}")
        
        # Step 4: Generate test
        print(f"\n4. Generating test for week {week_number}...")
        test_request = {
            "week_number": week_number,
            "difficulty": "medium",
            "question_types": ["mcq", "true_false"],
            "question_count": 5
        }
        
        test_response = await client.post(
            f"{BASE_URL}/tests/generate",
            params={"course_id": course_id},
            json=test_request,
            headers=headers
        )
        
        if test_response.status_code != 201:
            print(f"❌ Test generation failed: {test_response.status_code}")
            print(f"   Error: {test_response.text}")
            return
        
        test = test_response.json()
        print("✅ Test generated successfully!")
        print(f"   Test ID: {test['id']}")
        print(f"   Title: {test['title']}")
        print(f"   Difficulty: {test['difficulty']}")
        print(f"   Total Points: {test['total_points']}")
        print(f"   Time Limit: {test['time_limit']} minutes")
        print(f"   Questions: {len(test['questions'])}")
        
        # Display questions
        print("\n5. Generated Questions:")
        print("-" * 60)
        for i, q in enumerate(test['questions'], 1):
            print(f"\nQuestion {i} ({q['type'].upper()}) - {q['points']} points")
            print(f"Difficulty: {q['difficulty']} | Bloom: {q.get('bloom_level', 'N/A')}")
            print(f"Q: {q['question_text']}")
            
            if q.get('options'):
                for j, option in enumerate(q['options'], 1):
                    marker = "✓" if option == q.get('correct_answer') else " "
                    print(f"   {marker} {j}. {option}")
            else:
                print(f"   Answer: {q.get('correct_answer')}")
        
        print("\n" + "=" * 60)
        print("✅ TEST GENERATION WORKFLOW COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_test_generation())
