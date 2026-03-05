"""Lecture processing background tasks."""
import asyncio
from celery import Task
from celery.utils.log import get_task_logger

from src.4_infrastructure.queue.celery_app import celery_app
from src.4_infrastructure.database.connection import async_session_maker
from src.2_application.orchestrators.agent_orchestrator import AgentOrchestrator
from src.4_infrastructure.database.repositories.lecture_repository import LectureRepository

logger = get_task_logger(__name__)


class AsyncTask(Task):
    """Custom Celery task class for async functions."""
    
    def __call__(self, *args, **kwargs):
        """Run async function in event loop."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(*args, **kwargs))
    
    async def run(self, *args, **kwargs):
        """Override this method in subclasses."""
        raise NotImplementedError()


@celery_app.task(
    bind=True,
    base=AsyncTask,
    name="lecture_processing.process_lecture",
    max_retries=3,
    default_retry_delay=60
)
async def process_lecture_task(self, lecture_id: str):
    """
    Background task: Process lecture with AI.
    
    Args:
        lecture_id: Lecture ID
        
    Returns:
        dict with processing result
    """
    logger.info(f"Starting lecture processing: {lecture_id}")
    
    try:
        # Create async database session
        async with async_session_maker() as session:
            # Initialize repositories
            lecture_repo = LectureRepository(session)
            
            # Get lecture
            db_lecture = await lecture_repo.get_by_id(lecture_id)
            if not db_lecture:
                raise ValueError(f"Lecture {lecture_id} not found")
            
            # Validate lecture has content
            if not db_lecture.content:
                raise ValueError("Lecture has no content to process")
            
            # Mark as processing
            db_lecture.status = "processing"
            await session.commit()
            
            # Initialize orchestrator
            orchestrator = AgentOrchestrator(session)
            
            # Execute processing
            result = await orchestrator.process_lecture(
                lecture_id=lecture_id,
                content=db_lecture.content,
                title=db_lecture.title
            )
            
            logger.info(f"Lecture processing completed: {lecture_id}")
            
            return {
                "lecture_id": lecture_id,
                "status": "completed",
                "chunks_created": result["chunks_created"],
                "key_concepts": result["key_concepts"],
                "summary": result["summary"]
            }
    
    except Exception as exc:
        logger.error(f"Lecture processing failed: {lecture_id}, Error: {str(exc)}")
        
        # Update lecture status to failed
        try:
            async with async_session_maker() as session:
                lecture_repo = LectureRepository(session)
                db_lecture = await lecture_repo.get_by_id(lecture_id)
                if db_lecture:
                    db_lecture.status = "failed"
                    await session.commit()
        except Exception as e:
            logger.error(f"Failed to update lecture status: {str(e)}")
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(name="lecture_processing.test_task")
def test_celery_task(x: int, y: int):
    """Simple test task."""
    logger.info(f"Test task: {x} + {y}")
    return x + y
