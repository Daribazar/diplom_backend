#!/usr/bin/env python3
"""
Complete workflow test with PDF upload
Tests the entire flow: Auth -> Course -> Lecture -> Test -> Evaluation
"""
import asyncio
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/api/v1"

TEST_USER = {
    "email": "workflow@example.com",
    "password": "workflow123",
    "full_name": "Workflow Test User",
}


def create_test_pdf():
    """Create a simple test PDF with lecture content"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Add content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Neural Networks - Lecture 1")

    c.setFont("Helvetica", 12)
    y = 700
    content = [
        "",
        "Introduction to Neural Networks",
        "",
        "A neural network is a computational model inspired by biological neural networks.",
        "It consists of interconnected nodes (neurons) organized in layers.",
        "",
        "Key Concepts:",
        "1. Input Layer: Receives input data",
        "2. Hidden Layers: Process information",
        "3. Output Layer: Produces final result",
        "4. Weights: Connection strengths between neurons",
        "5. Activation Functions: Introduce non-linearity (ReLU, Sigmoid, Tanh)",
        "6. Backpropagation: Algorithm for training networks",
        "",
        "Types of Neural Networks:",
        "- Feedforward Neural Networks",
        "- Convolutional Neural Networks (CNN)",
        "- Recurrent Neural Networks (RNN)",
        "",
        "Applications:",
        "- Image recognition",
        "- Natural language processing",
        "- Speech recognition",
        "- Game playing (AlphaGo)",
    ]

    for line in content:
        c.drawString(100, y, line)
        y -= 20

    c.save()
    buffer.seek(0)
    return buffer


async def test_complete_workflow():
    """Test complete workflow"""
    print("\n" + "=" * 80)
    print("COMPLETE WORKFLOW TEST".center(80))
    print("=" * 80)

    token = None
    course_id = None
    lecture_id = None
    test_id = None

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Register/Login
        print("\n1️⃣  Authentication...")
        try:
            response = await client.post(f"{API_BASE}/auth/register", json=TEST_USER)
            if response.status_code == 201:
                print("✅ User registered")
            elif response.status_code == 409:
                print("⚠️  User exists, logging in...")
        except Exception as e:
            print(f"⚠️  Register: {e}")

        # Login
        response = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": TEST_USER["email"], "password": TEST_USER["password"]},
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"✅ Logged in successfully")
        else:
            print(f"❌ Login failed: {response.status_code}")
            return

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Course
        print("\n2️⃣  Creating course...")
        response = await client.post(
            f"{API_BASE}/courses",
            json={
                "name": "Deep Learning Course",
                "code": "DL101",
                "semester": "Spring 2024",
                "instructor": "Prof. AI",
            },
            headers=headers,
        )
        if response.status_code == 201:
            course_id = response.json()["id"]
            print(f"✅ Course created: {course_id}")
        else:
            print(f"❌ Course creation failed: {response.status_code}")
            return

        # 3. Upload Lecture
        print("\n3️⃣  Uploading lecture PDF...")
        pdf_buffer = create_test_pdf()

        files = {"file": ("lecture1.pdf", pdf_buffer, "application/pdf")}
        data = {
            "course_id": course_id,
            "week_number": "1",
            "title": "Introduction to Neural Networks",
        }

        response = await client.post(
            f"{API_BASE}/lectures/upload", files=files, data=data, headers=headers
        )

        if response.status_code == 201:
            lecture_data = response.json()
            lecture_id = lecture_data["id"]
            print(f"✅ Lecture uploaded: {lecture_id}")
            print(f"   Status: {lecture_data.get('status')}")
            print(f"   Message: {lecture_data.get('message')}")
        else:
            print(f"❌ Lecture upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        # 4. Wait for processing and check status
        print("\n4️⃣  Waiting for lecture processing...")
        max_attempts = 30
        for attempt in range(max_attempts):
            await asyncio.sleep(2)

            response = await client.get(
                f"{API_BASE}/lectures/{lecture_id}/status", headers=headers
            )

            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status")
                print(f"   Attempt {attempt + 1}/{max_attempts}: Status = {status}")

                if status == "completed":
                    print(f"✅ Lecture processed successfully!")
                    print(f"   Key concepts: {status_data.get('key_concepts', [])}")
                    break
                elif status == "failed":
                    print(f"❌ Lecture processing failed")
                    return
            else:
                print(f"⚠️  Status check failed: {response.status_code}")
        else:
            print(f"⚠️  Processing timeout after {max_attempts * 2} seconds")
            print("   Continuing anyway...")

        # 5. Generate Test
        print("\n5️⃣  Generating test...")
        response = await client.post(
            f"{API_BASE}/tests/generate?course_id={course_id}",
            json={
                "week_number": 1,
                "num_mcq": 3,
                "num_true_false": 2,
                "num_essay": 1,
                "difficulty": "medium",
            },
            headers=headers,
        )

        if response.status_code == 201:
            test_data = response.json()
            test_id = test_data["id"]
            print(f"✅ Test generated: {test_id}")
            print(f"   Total questions: {len(test_data.get('questions', []))}")
            print(f"   Total points: {test_data.get('total_points')}")

            # Show questions
            for i, q in enumerate(test_data.get("questions", []), 1):
                print(f"\n   Question {i} ({q['type']}):")
                print(f"   {q['question'][:80]}...")
        else:
            print(f"❌ Test generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        # 6. Submit Test
        print("\n6️⃣  Submitting test answers...")

        # Prepare answers
        answers = []
        for q in test_data.get("questions", []):
            if q["type"] == "mcq":
                # Pick first option
                answers.append(
                    {
                        "question_id": q["id"],
                        "answer": q["options"][0] if q.get("options") else "A",
                    }
                )
            elif q["type"] == "true_false":
                answers.append({"question_id": q["id"], "answer": "True"})
            elif q["type"] == "essay":
                answers.append(
                    {
                        "question_id": q["id"],
                        "answer": "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes organized in layers.",
                    }
                )

        response = await client.post(
            f"{API_BASE}/evaluations/submit/{test_id}",
            json={"answers": answers},
            headers=headers,
        )

        if response.status_code == 201:
            eval_data = response.json()
            attempt_id = eval_data["attempt_id"]
            print(f"✅ Test submitted: {attempt_id}")
            print(f"   Score: {eval_data.get('score')}/{eval_data.get('max_score')}")
            print(f"   Percentage: {eval_data.get('percentage')}%")
            print(f"   Feedback: {eval_data.get('feedback', '')[:100]}...")
        else:
            print(f"❌ Test submission failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        # 7. Get Attempt Details
        print("\n7️⃣  Getting attempt details...")
        response = await client.get(
            f"{API_BASE}/evaluations/attempt/{attempt_id}", headers=headers
        )

        if response.status_code == 200:
            attempt_data = response.json()
            print(f"✅ Attempt details retrieved")
            print(
                f"   Score: {attempt_data.get('score')}/{attempt_data.get('max_score')}"
            )
            print(f"   Percentage: {attempt_data.get('percentage')}%")
        else:
            print(f"❌ Get attempt failed: {response.status_code}")

    print("\n" + "=" * 80)
    print("✅ COMPLETE WORKFLOW TEST FINISHED".center(80))
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
