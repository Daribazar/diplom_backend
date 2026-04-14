#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script
Tests all endpoints that frontend will use
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
import json


class Console:
    """Simple console replacement"""

    def print(self, *args, **kwargs):
        print(*args)


console = Console()

BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
TEST_USER = {
    "email": "test@example.com",
    "password": "test123456",
    "full_name": "Test User",
}

TEST_COURSE = {
    "name": "Test Course",
    "code": "TEST101",
    "semester": "Spring 2024",
    "instructor": "Test Instructor",
}


class EndpointTester:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.course_id = None
        self.lecture_id = None
        self.test_id = None
        self.attempt_id = None
        self.results = []

    def add_result(
        self, category: str, endpoint: str, method: str, status: str, message: str = ""
    ):
        """Add test result"""
        self.results.append(
            {
                "category": category,
                "endpoint": endpoint,
                "method": method,
                "status": status,
                "message": message,
            }
        )

    async def test_health(self):
        """Test system health endpoints"""
        print("\n" + "=" * 60)
        print("Testing System Health")
        print("=" * 60)

        async with httpx.AsyncClient() as client:
            # Test root endpoint
            try:
                response = await client.get(f"{BASE_URL}/")
                if response.status_code == 200:
                    console.print("✅ Root endpoint: OK")
                    self.add_result("System", "/", "GET", "✅ PASS")
                else:
                    console.print(f"❌ Root endpoint: Failed ({response.status_code})")
                    self.add_result(
                        "System",
                        "/",
                        "GET",
                        "❌ FAIL",
                        f"Status: {response.status_code}",
                    )
            except Exception as e:
                console.print(f"❌ Root endpoint: Error - {e}")
                self.add_result("System", "/", "GET", "❌ ERROR", str(e))

            # Test health endpoint
            try:
                response = await client.get(f"{BASE_URL}/health")
                if response.status_code == 200:
                    data = response.json()
                    console.print(f"✅ Health check: {data}")
                    self.add_result(
                        "System",
                        "/health",
                        "GET",
                        "✅ PASS",
                        f"DB: {data.get('database')}, Redis: {data.get('redis')}",
                    )
                else:
                    console.print(f"❌ Health check: Failed")
                    self.add_result("System", "/health", "GET", "❌ FAIL")
            except Exception as e:
                console.print(f"❌ Health check: Error - {e}")
                self.add_result("System", "/health", "GET", "❌ ERROR", str(e))

    async def test_auth(self):
        """Test authentication endpoints"""
        print("\n" + "=" * 60)
        print("Testing Authentication")
        print("=" * 60)

        async with httpx.AsyncClient() as client:
            # 1. Register
            try:
                response = await client.post(
                    f"{API_BASE}/auth/register", json=TEST_USER
                )
                if response.status_code == 201:
                    data = response.json()
                    self.user_id = data.get("id")
                    console.print(f"✅ Register: User created - {self.user_id}")
                    self.add_result(
                        "Auth",
                        "/auth/register",
                        "POST",
                        "✅ PASS",
                        f"User ID: {self.user_id}",
                    )
                elif response.status_code == 409:
                    console.print("⚠️  Register: User already exists (OK)")
                    self.add_result(
                        "Auth", "/auth/register", "POST", "⚠️  SKIP", "User exists"
                    )
                else:
                    console.print(f"❌ Register: Failed ({response.status_code})")
                    self.add_result(
                        "Auth",
                        "/auth/register",
                        "POST",
                        "❌ FAIL",
                        f"Status: {response.status_code}",
                    )
            except Exception as e:
                console.print(f"❌ Register: Error - {e}")
                self.add_result("Auth", "/auth/register", "POST", "❌ ERROR", str(e))

            # 2. Login
            try:
                response = await client.post(
                    f"{API_BASE}/auth/login",
                    json={
                        "email": TEST_USER["email"],
                        "password": TEST_USER["password"],
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    console.print(f"✅ Login: Token received")
                    self.add_result(
                        "Auth", "/auth/login", "POST", "✅ PASS", "Token received"
                    )
                else:
                    console.print(f"❌ Login: Failed ({response.status_code})")
                    self.add_result(
                        "Auth",
                        "/auth/login",
                        "POST",
                        "❌ FAIL",
                        f"Status: {response.status_code}",
                    )
                    return False
            except Exception as e:
                console.print(f"❌ Login: Error - {e}")
                self.add_result("Auth", "/auth/login", "POST", "❌ ERROR", str(e))
                return False

            # 3. Get current user
            if self.token:
                try:
                    response = await client.get(
                        f"{API_BASE}/auth/me",
                        headers={"Authorization": f"Bearer {self.token}"},
                    )
                    if response.status_code == 200:
                        data = response.json()
                        console.print(f"✅ Get user: {data.get('email')}")
                        self.add_result(
                            "Auth",
                            "/auth/me",
                            "GET",
                            "✅ PASS",
                            f"Email: {data.get('email')}",
                        )
                    else:
                        console.print(f"❌ Get user: Failed")
                        self.add_result("Auth", "/auth/me", "GET", "❌ FAIL")
                except Exception as e:
                    console.print(f"❌ Get user: Error - {e}")
                    self.add_result("Auth", "/auth/me", "GET", "❌ ERROR", str(e))

        return True

    async def test_courses(self):
        """Test course endpoints"""
        print("\n" + "=" * 60)
        print("Testing Courses")
        print("=" * 60)

        if not self.token:
            console.print("❌ No token available, skipping course tests")
            return False

        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient() as client:
            # 1. Create course
            try:
                response = await client.post(
                    f"{API_BASE}/courses", json=TEST_COURSE, headers=headers
                )
                if response.status_code == 201:
                    data = response.json()
                    self.course_id = data.get("id")
                    console.print(f"✅ Create course: {self.course_id}")
                    self.add_result(
                        "Courses",
                        "/courses",
                        "POST",
                        "✅ PASS",
                        f"Course ID: {self.course_id}",
                    )
                else:
                    console.print(f"❌ Create course: Failed ({response.status_code})")
                    self.add_result(
                        "Courses",
                        "/courses",
                        "POST",
                        "❌ FAIL",
                        f"Status: {response.status_code}",
                    )
                    return False
            except Exception as e:
                console.print(f"❌ Create course: Error - {e}")
                self.add_result("Courses", "/courses", "POST", "❌ ERROR", str(e))
                return False

            # 2. Get all courses
            try:
                response = await client.get(f"{API_BASE}/courses", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    console.print(f"✅ Get courses: {data.get('total')} courses")
                    self.add_result(
                        "Courses",
                        "/courses",
                        "GET",
                        "✅ PASS",
                        f"Total: {data.get('total')}",
                    )
                else:
                    console.print(f"❌ Get courses: Failed")
                    self.add_result("Courses", "/courses", "GET", "❌ FAIL")
            except Exception as e:
                console.print(f"❌ Get courses: Error - {e}")
                self.add_result("Courses", "/courses", "GET", "❌ ERROR", str(e))

            # 3. Get single course
            if self.course_id:
                try:
                    response = await client.get(
                        f"{API_BASE}/courses/{self.course_id}", headers=headers
                    )
                    if response.status_code == 200:
                        data = response.json()
                        console.print(f"✅ Get course: {data.get('name')}")
                        self.add_result(
                            "Courses", f"/courses/{'{id}'}", "GET", "✅ PASS"
                        )
                    else:
                        console.print(f"❌ Get course: Failed")
                        self.add_result(
                            "Courses", f"/courses/{'{id}'}", "GET", "❌ FAIL"
                        )
                except Exception as e:
                    console.print(f"❌ Get course: Error - {e}")
                    self.add_result(
                        "Courses", f"/courses/{'{id}'}", "GET", "❌ ERROR", str(e)
                    )

            # 4. Update course
            if self.course_id:
                try:
                    response = await client.patch(
                        f"{API_BASE}/courses/{self.course_id}",
                        json={"name": "Updated Test Course"},
                        headers=headers,
                    )
                    if response.status_code == 200:
                        console.print(f"✅ Update course: Success")
                        self.add_result(
                            "Courses", f"/courses/{'{id}'}", "PATCH", "✅ PASS"
                        )
                    else:
                        console.print(f"❌ Update course: Failed")
                        self.add_result(
                            "Courses", f"/courses/{'{id}'}", "PATCH", "❌ FAIL"
                        )
                except Exception as e:
                    console.print(f"❌ Update course: Error - {e}")
                    self.add_result(
                        "Courses", f"/courses/{'{id}'}", "PATCH", "❌ ERROR", str(e)
                    )

        return True

    async def test_lectures(self):
        """Test lecture endpoints"""
        print("\n" + "=" * 60)
        print("Testing Lectures")
        print("=" * 60)

        if not self.token or not self.course_id:
            console.print("❌ No token or course_id, skipping lecture tests")
            return False

        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient() as client:
            # 1. Get course lectures (should be empty initially)
            try:
                response = await client.get(
                    f"{API_BASE}/lectures/course/{self.course_id}", headers=headers
                )
                if response.status_code == 200:
                    data = response.json()
                    console.print(f"✅ Get lectures: {data.get('total')} lectures")
                    self.add_result(
                        "Lectures",
                        f"/lectures/course/{'{id}'}",
                        "GET",
                        "✅ PASS",
                        f"Total: {data.get('total')}",
                    )
                else:
                    console.print(f"❌ Get lectures: Failed")
                    self.add_result(
                        "Lectures", f"/lectures/course/{'{id}'}", "GET", " FAIL"
                    )
            except Exception as e:
                console.print(f" Get lectures: Error - {e}")
                self.add_result(
                    "Lectures", f"/lectures/course/{'{id}'}", "GET", " ERROR", str(e)
                )

            # Note: File upload test requires actual PDF file
            console.print("⚠️  Lecture upload requires PDF file (skipping)")
            self.add_result(
                "Lectures", "/lectures/upload", "POST", "  SKIP", "Requires PDF file"
            )

        return True

    async def test_tests(self):
        """Test test generation endpoints"""
        print("\n" + "=" * 60)
        print("Testing Test Generation")
        print("=" * 60)

        if not self.token or not self.course_id:
            console.print(" No token or course_id, skipping test generation")
            return False

        headers = {"Authorization": f"Bearer {self.token}"}

        async with httpx.AsyncClient() as client:
            # Note: Test generation requires processed lecture
            console.print("  Test generation requires processed lecture (skipping)")
            self.add_result(
                "Tests", "/tests/generate", "POST", " SKIP", "Requires lecture"
            )
            self.add_result(
                "Tests", f"/tests/{'{id}'}", "GET", "  SKIP", "Requires test"
            )
            self.add_result(
                "Tests",
                f"/tests/lecture/{'{id}'}",
                "GET",
                "  SKIP",
                "Requires lecture",
            )

        return True

    async def test_evaluations(self):
        """Test evaluation endpoints"""
        print("\n" + "=" * 60)
        print("Testing Evaluations")
        print("=" * 60)

        if not self.token:
            console.print(" No token, skipping evaluation tests")
            return False

        # Note: Evaluation requires test submission
        console.print("  Evaluation requires test submission (skipping)")
        self.add_result(
            "Evaluations",
            f"/evaluations/submit/{'{id}'}",
            "POST",
            "SKIP",
            "Requires test",
        )
        self.add_result(
            "Evaluations",
            f"/evaluations/attempt/{'{id}'}",
            "GET",
            "SKIP",
            "Requires attempt",
        )
        self.add_result(
            "Evaluations",
            f"/evaluations/test/{'{id}'}/attempts",
            "GET",
            "SKIP",
            "Requires test",
        )

        return True

    def print_summary(self):
        """Print test summary table"""
        print("\n" + "=" * 100)
        print("TEST RESULTS SUMMARY".center(100))
        print("=" * 100)

        # Print header
        print(
            f"\n{'Category':<15} {'Endpoint':<35} {'Method':<8} {'Status':<12} {'Message':<30}"
        )
        print("-" * 100)

        # Print results
        for result in self.results:
            print(
                f"{result['category']:<15} {result['endpoint']:<35} {result['method']:<8} {result['status']:<12} {result['message']:<30}"
            )

        # Count results
        total = len(self.results)
        passed = sum(1 for r in self.results if "✅" in r["status"])
        failed = sum(1 for r in self.results if "❌" in r["status"])
        skipped = sum(1 for r in self.results if "⚠️" in r["status"])

        print("\n" + "=" * 100)
        print("\nSUMMARY:")
        print(f"  Total Tests: {total}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Skipped: {skipped}")

        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")

    async def run_all_tests(self):
        """Run all endpoint tests"""
        print("\n" + "=" * 100)
        print("Agentic AI student support system - COMPREHENSIVE API TESTING".center(100))
        print("Testing all endpoints for frontend integration".center(100))
        print("=" * 100)

        # Run tests in order
        await self.test_health()

        auth_ok = await self.test_auth()
        if not auth_ok:
            console.print(
                "\n[bold red]❌ Authentication failed, stopping tests[/bold red]"
            )
            self.print_summary()
            return

        await self.test_courses()
        await self.test_lectures()
        await self.test_tests()
        await self.test_evaluations()

        # Print summary
        self.print_summary()


async def main():
    """Main test runner"""
    tester = EndpointTester()

    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
