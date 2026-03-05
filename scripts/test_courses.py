"""Test course endpoints."""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx


BASE_URL = "http://localhost:8000"


async def test_course_crud():
    """Test complete course CRUD operations."""
    print("🧪 Testing Course CRUD Operations\n")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Register and login to get token
        print("1️⃣ Setting up authentication...")
        
        # Register
        register_data = {
            "email": "course_test@example.com",
            "password": "testpassword123",
            "full_name": "Course Test User"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=register_data
        )
        
        if response.status_code == 409:
            print("   ⚠️  User already exists, logging in...")
        elif response.status_code == 201:
            print("   ✅ User registered")
        else:
            print(f"   ❌ Registration failed: {response.status_code}")
            return False
        
        # Login
        login_data = {
            "email": "course_test@example.com",
            "password": "testpassword123"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json=login_data
        )
        
        if response.status_code != 200:
            print(f"   ❌ Login failed: {response.status_code}")
            return False
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("   ✅ Authentication successful\n")
        
        # Step 2: Create course
        print("2️⃣ Testing course creation (POST /courses)...")
        course_data = {
            "name": "Introduction to Machine Learning",
            "code": "CS401",
            "semester": "Fall 2024",
            "instructor": "Prof. Smith"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/v1/courses",
            json=course_data,
            headers=headers
        )
        
        if response.status_code != 201:
            print(f"   ❌ Course creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        course = response.json()
        course_id = course["id"]
        print(f"   ✅ Course created: {course['name']}")
        print(f"   Course ID: {course_id}")
        print(f"   Code: {course['code']}, Semester: {course['semester']}\n")
        
        # Step 3: Get all courses
        print("3️⃣ Testing get all courses (GET /courses)...")
        response = await client.get(
            f"{BASE_URL}/api/v1/courses",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"   ❌ Get courses failed: {response.status_code}")
            return False
        
        courses_list = response.json()
        print(f"   ✅ Retrieved {courses_list['total']} course(s)")
        for c in courses_list['courses']:
            print(f"      - {c['name']} ({c['code']})\n")
        
        # Step 4: Get single course
        print(f"4️⃣ Testing get single course (GET /courses/{course_id})...")
        response = await client.get(
            f"{BASE_URL}/api/v1/courses/{course_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"   ❌ Get course failed: {response.status_code}")
            return False
        
        course = response.json()
        print(f"   ✅ Retrieved course: {course['name']}")
        print(f"   Instructor: {course['instructor']}\n")
        
        # Step 5: Update course
        print(f"5️⃣ Testing course update (PATCH /courses/{course_id})...")
        update_data = {
            "name": "Advanced Machine Learning",
            "instructor": "Prof. Johnson"
        }
        
        response = await client.patch(
            f"{BASE_URL}/api/v1/courses/{course_id}",
            json=update_data,
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"   ❌ Course update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        updated_course = response.json()
        print(f"   ✅ Course updated")
        print(f"   New name: {updated_course['name']}")
        print(f"   New instructor: {updated_course['instructor']}\n")
        
        # Step 6: Test authorization (try to access with invalid token)
        print("6️⃣ Testing authorization (invalid token)...")
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        response = await client.get(
            f"{BASE_URL}/api/v1/courses/{course_id}",
            headers=invalid_headers
        )
        
        if response.status_code == 401:
            print("   ✅ Unauthorized access correctly rejected\n")
        else:
            print(f"   ❌ Expected 401, got {response.status_code}\n")
        
        # Step 7: Delete course
        print(f"7️⃣ Testing course deletion (DELETE /courses/{course_id})...")
        response = await client.delete(
            f"{BASE_URL}/api/v1/courses/{course_id}",
            headers=headers
        )
        
        if response.status_code != 204:
            print(f"   ❌ Course deletion failed: {response.status_code}")
            return False
        
        print("   ✅ Course deleted successfully\n")
        
        # Step 8: Verify deletion
        print("8️⃣ Verifying course was deleted...")
        response = await client.get(
            f"{BASE_URL}/api/v1/courses/{course_id}",
            headers=headers
        )
        
        if response.status_code == 404:
            print("   ✅ Course not found (correctly deleted)\n")
        else:
            print(f"   ❌ Expected 404, got {response.status_code}\n")
            return False
    
    print("="*50)
    print("✅ All course CRUD tests passed!")
    print("="*50)
    return True


async def main():
    """Main test function."""
    print("Starting course CRUD tests...")
    print("Make sure the server is running: poetry run python src/main.py\n")
    
    try:
        success = await test_course_crud()
        sys.exit(0 if success else 1)
    except httpx.ConnectError:
        print("\n❌ Could not connect to server.")
        print("Please start the server first: poetry run python src/main.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
