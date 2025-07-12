from app.core.config import settings
from app.utils.logger import get_logger
from app.utils.db_connect import mongodb
from app.core.celery_worker_service import process_message_inside_task_queue
from app.core.pinecone_config import pinecone
from app.core.embeddings_config import embeddings

from celery import Celery
from celery.signals import worker_process_init
import asyncio

logger = get_logger("worker")

celery = Celery(
    'worker',
    broker=settings.BROKER_URL,
    backend=settings.BACKEND_URL
)

# Configure Celery settings
celery.conf.update(
    # Worker settings
    worker_concurrency=1,  # Number of worker processes
    worker_prefetch_multiplier=1,  # How many tasks a worker can reserve
    task_acks_late=True,  # Acknowledge tasks after they complete
    worker_max_tasks_per_child=1000,  # Restart workers after N tasks (prevents memory leaks)
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
)

logger.info("Starting DB Connection in Celery Tasks")
'''
    Used To Connect Mongo in Celery Tasks
    Celery is Synchronous by default and therefore has to use asyncio
    In FastAPI the async-await uses asyncio under the hood, but is managed by uvicorn

    Will be called when Celery App is started
'''
@worker_process_init.connect
def init_worker(**kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Initialize MongoDB connection
    loop.run_until_complete(mongodb.connect())
    logger.info("DB Connected in Celery Tasks")
    
    # Initialize Pinecone connection
    try:
        if not pinecone.is_initialized():
            loop.run_until_complete(pinecone.initialize_connection())
            logger.info("Pinecone Connected in Celery Tasks")
        else:
            logger.info("Pinecone already initialized in Celery Tasks")
    except Exception as e:
        logger.error(f"Failed to initialize Pinecone connection: {str(e)}")
    
    # Initialize Embeddings config
    try:
        if not embeddings.is_initialized():
            loop.run_until_complete(embeddings.initialize_embeddings())
            logger.info("Embeddings Config Initialized in Celery Tasks")
        else:
            logger.info("Embeddings already initialized in Celery Tasks")
    except Exception as e:
        logger.error(f"Failed to initialize embeddings config: {str(e)}")

@celery.task
def process_message_task(message_id : str):
    async def safe_wrapper():
        return await process_message_inside_task_queue(message_id)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already running (e.g., inside a thread, Jupyter), create a new one
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            return new_loop.run_until_complete(safe_wrapper())
        else:
            return loop.run_until_complete(safe_wrapper())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(safe_wrapper())