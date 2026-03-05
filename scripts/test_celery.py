"""Test Celery setup."""
import asyncio
from src.4_infrastructure.queue.tasks.lecture_processing import test_celery_task


def test_simple_task():
    """Test simple Celery task."""
    print("Testing Celery task...")
    
    # Send task to Celery
    result = test_celery_task.delay(5, 10)
    
    print(f"Task ID: {result.id}")
    print(f"Task State: {result.state}")
    
    # Wait for result (with timeout)
    try:
        output = result.get(timeout=10)
        print(f"Result: {output}")
        print("✅ Celery is working!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Make sure Redis and Celery worker are running:")
        print("  Terminal 1: redis-server")
        print("  Terminal 2: ./scripts/run_celery.sh")


if __name__ == "__main__":
    test_simple_task()
