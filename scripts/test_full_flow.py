"""Test complete system flow from registration to evaluation."""

import asyncio
import httpx
import json


BASE_URL = "http://localhost:8000/api/v1"


async def test_complete_flow():
    """Test complete Agentic AI student support system flow."""
    print("=" * 70)
    print("Agentic AI student support system - COMPLETE SYSTEM TEST")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Register/Login
        print("\n📝 Step 1: Authentication")
        print("-" * 70)

        login_response = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "test@example.com", "password": "password123"},
        )

        if login_response.status_code != 200:
            print("❌ Login failed. Registering new user...")
            register_response = await client.post(
                f"{BASE_URL}/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "password123",
                    "full_name": "Test Student",
                },
            )
            if register_response.status_code == 201:
                print("✅ User registered successfully")
                token = register_response.json()["access_token"]
            else:
                print(f"❌ Registration failed: {register_response.text}")
                return
        else:
            token = login_response.json()["access_token"]
            print("✅ Logged in successfully")

        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Create Course
        print("\n📚 Step 2: Create Course")
        print("-" * 70)

        courses_response = await client.get(f"{BASE_URL}/courses", headers=headers)

        if courses_response.json()["courses"]:
            course = courses_response.json()["courses"][0]
            course_id = course["id"]
            print(f"✅ Using existing course: {course['title']} ({course_id})")
        else:
            create_course_response = await client.post(
                f"{BASE_URL}/courses",
                headers=headers,
                json={
                    "title": "Machine Learning 101",
                    "description": "Introduction to Machine Learning",
                },
            )
            if create_course_response.status_code == 201:
                course = create_course_response.json()
                course_id = course["id"]
                print(f"✅ Course created: {course['title']} ({course_id})")
            else:
                print(f"❌ Course creation failed: {create_course_response.text}")
                return

        # Step 3: Check Lectures
        print("\n📄 Step 3: Check Lectures")
        print("-" * 70)

        lectures_response = await client.get(
            f"{BASE_URL}/lectures/course/{course_id}", headers=headers
        )

        if lectures_response.status_code != 200:
            print("❌ Failed to get lectures")
            return

        lectures = lectures_response.json()["lectures"]

        if not lectures:
            print("❌ No lectures found. Please upload a lecture first:")
            print("   curl -X POST http://localhost:8000/api/v1/lectures/upload \\")
            print("     -H 'Authorization: Bearer TOKEN' \\")
            print(f"     -F 'course_id={course_id}' \\")
            print("     -F 'week_number=1' \\")
            print("     -F 'title=Introduction' \\")
            print("     -F 'file=@lecture.pdf'")
            return

        # Find completed lecture
        completed_lecture = None
        for lecture in lectures:
            if lecture["status"] == "completed":
                completed_lecture = lecture
                break

        if not completed_lecture:
            print("⏳ No completed lectures. Status of lectures:")
            for lec in lectures:
                print(f"   - Week {lec['week_number']}: {lec['status']}")
            print("\n   Wait for processing to complete or check status:")
            print(f"   GET /api/v1/lectures/{{lecture_id}}/status")
            return

        week_number = completed_lecture["week_number"]
        print(
            f"✅ Found completed lecture: Week {week_number} - {completed_lecture['title']}"
        )
        print(
            f"   Key concepts: {', '.join(completed_lecture.get('key_concepts', [])[:3])}..."
        )

        # Step 4: Generate Test
        print("\n🧪 Step 4: Generate Test")
        print("-" * 70)

        test_request = {
            "week_number": week_number,
            "difficulty": "medium",
            "question_types": ["mcq", "true_false"],
            "question_count": 5,
        }

        test_response = await client.post(
            f"{BASE_URL}/tests/generate",
            params={"course_id": course_id},
            json=test_request,
            headers=headers,
        )

        if test_response.status_code != 201:
            print(f"❌ Test generation failed: {test_response.text}")
            return

        test = test_response.json()
        test_id = test["id"]
        print(f"✅ Test generated successfully!")
        print(f"   Test ID: {test_id}")
        print(f"   Title: {test['title']}")
        print(f"   Questions: {len(test['questions'])}")
        print(f"   Total Points: {test['total_points']}")

        # Display questions
        print("\n📋 Generated Questions:")
        for i, q in enumerate(test["questions"], 1):
            print(f"\n   Q{i}. [{q['type'].upper()}] {q['question_text'][:60]}...")
            if q.get("options"):
                for j, opt in enumerate(q["options"][:2], 1):
                    print(f"       {j}. {opt[:40]}...")

        # Step 5: Submit Test
        print("\n✍️  Step 5: Submit Test Answers")
        print("-" * 70)

        # Prepare answers (simulate student answers)
        answers = []
        for q in test["questions"]:
            if q["type"] == "mcq":
                # Pick first option (may be wrong)
                answer = q["options"][0] if q.get("options") else ""
            elif q["type"] == "true_false":
                # Pick True
                answer = "True"
            else:
                # Essay
                answer = "This is a sample essay answer."

            answers.append({"question_id": q["question_id"], "answer": answer})

        submit_response = await client.post(
            f"{BASE_URL}/evaluations/submit/{test_id}",
            headers=headers,
            json={"answers": answers},
        )

        if submit_response.status_code != 201:
            print(f"❌ Test submission failed: {submit_response.text}")
            return

        evaluation = submit_response.json()

        # Step 6: Display Results
        print("\n🎯 Step 6: Evaluation Results")
        print("=" * 70)

        print(
            f"\n📊 SCORE: {evaluation['total_score']}/{test['total_points']} ({evaluation['percentage']:.1f}%)"
        )
        print(f"📈 STATUS: {evaluation['status']}")

        if evaluation["weak_topics"]:
            print(f"\n⚠️  WEAK TOPICS: {', '.join(evaluation['weak_topics'])}")
        else:
            print("\n✅ NO WEAK TOPICS - Great job!")

        print(f"\n💬 FEEDBACK (Mongolian):")
        print(f"   {evaluation['overall_feedback']}")

        print(f"\n📈 ANALYTICS:")
        analytics = evaluation["analytics"]
        print(f"   Overall Accuracy: {analytics['overall_accuracy']*100:.1f}%")

        if "by_difficulty" in analytics:
            print(f"\n   By Difficulty:")
            for diff, stats in analytics["by_difficulty"].items():
                acc = (
                    stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
                )
                print(
                    f"     - {diff.capitalize()}: {stats['correct']}/{stats['total']} ({acc:.0f}%)"
                )

        if "by_type" in analytics:
            print(f"\n   By Type:")
            for qtype, stats in analytics["by_type"].items():
                acc = (
                    stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
                )
                print(
                    f"     - {qtype.upper()}: {stats['correct']}/{stats['total']} ({acc:.0f}%)"
                )

        print(f"\n📝 DETAILED RESULTS:")
        for i, ans in enumerate(evaluation["answers"], 1):
            status = "✅" if ans["is_correct"] else "❌"
            print(
                f"\n   {status} Q{i}: {ans['points_earned']}/{ans['max_points']} points"
            )
            print(f"      Your answer: {ans['student_answer'][:50]}...")
            if not ans["is_correct"]:
                print(f"      Correct: {ans['correct_answer'][:50]}...")
            print(f"      Feedback: {ans['feedback'][:80]}...")

        print("\n" + "=" * 70)
        print("✅ COMPLETE SYSTEM TEST SUCCESSFUL!")
        print("=" * 70)
        print(f"\nAttempt ID: {evaluation['attempt_id']}")
        print(
            f"Retrieve later: GET /api/v1/evaluations/attempt/{evaluation['attempt_id']}"
        )


if __name__ == "__main__":
    print("\n🚀 Starting complete system test...")
    print("Make sure the following are running:")
    print("  1. PostgreSQL")
    print("  2. Redis")
    print("  3. FastAPI (uvicorn src.main:app --reload)")
    print("  4. Celery Worker (./scripts/run_celery.sh)")
    print("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")

    try:
        import time

        time.sleep(3)
        asyncio.run(test_complete_flow())
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
