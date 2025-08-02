"""
Job Manager for handling async Browser Use tasks
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import asynccontextmanager

from app.models import (
    Job, JobStatus, JobType, JobProgress, JobRequest, 
    SearchRequest, SearchResponse
)
from app.agents.rappi_agent import RappiAgent

logger = logging.getLogger(__name__)


class JobManager:
    """Manages job queue and execution for Browser Use tasks"""
    
    def __init__(self, max_workers: int = 2):
        self.jobs: Dict[str, Job] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.max_workers = max_workers
        self.workers_running = False
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.RLock()
        
        logger.info(f"JobManager initialized with {max_workers} workers")
    
    async def start_workers(self):
        """Start background workers to process jobs"""
        if self.workers_running:
            return
            
        self.workers_running = True
        logger.info("Starting job workers...")
        
        # Start worker tasks
        for i in range(self.max_workers):
            asyncio.create_task(self._worker(f"worker-{i}"))
    
    async def stop_workers(self):
        """Stop background workers"""
        self.workers_running = False
        logger.info("Stopping job workers...")
    
    def create_job(self, job_request: JobRequest) -> Job:
        """Create a new job and add it to the queue"""
        job = Job(
            job_type=job_request.job_type,
            job_data=job_request.job_data,
            priority=job_request.priority,
            timeout_seconds=job_request.timeout_seconds
        )
        
        with self.lock:
            self.jobs[job.id] = job
        
        # Add to queue (higher priority = lower number for priority queue)
        self.job_queue.put_nowait((job.priority, job.id))
        
        logger.info(f"Created job {job.id} of type {job.job_type}")
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 20) -> List[Job]:
        """List jobs, optionally filtered by status"""
        with self.lock:
            jobs = list(self.jobs.values())
        
        if status:
            jobs = [job for job in jobs if job.status == status]
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        return jobs[:limit]
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job and job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                logger.info(f"Cancelled job {job_id}")
                return True
        return False
    
    async def _worker(self, worker_name: str):
        """Background worker to process jobs"""
        logger.info(f"{worker_name} started")
        
        while self.workers_running:
            try:
                # Get next job from queue with timeout
                try:
                    priority, job_id = await asyncio.wait_for(
                        self.job_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Get job details
                with self.lock:
                    job = self.jobs.get(job_id)
                
                if not job or job.status != JobStatus.PENDING:
                    continue
                
                # Start job execution
                await self._execute_job(job, worker_name)
                
            except Exception as e:
                logger.error(f"{worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.info(f"{worker_name} stopped")
    
    async def _execute_job(self, job: Job, worker_name: str):
        """Execute a single job"""
        job_id = job.id
        logger.info(f"{worker_name} executing job {job_id}")
        
        try:
            # Mark job as running
            with self.lock:
                job.status = JobStatus.RUNNING
                job.started_at = datetime.now()
                job.progress.step_description = "Initializing..."
                job.progress.progress_percentage = 0.0
            
            # Execute based on job type
            if job.job_type == JobType.FOOD_SEARCH:
                result = await self._execute_food_search(job)
            elif job.job_type == JobType.HEALTH_CHECK:
                result = await self._execute_health_check(job)
            else:
                raise ValueError(f"Unknown job type: {job.job_type}")
            
            # Mark job as completed
            with self.lock:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                job.result = result
                job.progress.progress_percentage = 100.0
                job.progress.step_description = "Completed"
            
            logger.info(f"{worker_name} completed job {job_id}")
            
        except Exception as e:
            # Mark job as failed
            logger.error(f"{worker_name} failed job {job_id}: {e}")
            
            with self.lock:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                job.error_message = str(e)
                job.progress.step_description = f"Failed: {str(e)}"
                
                # Retry logic
                if job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.status = JobStatus.PENDING
                    job.started_at = None
                    job.completed_at = None
                    job.error_message = None
                    job.progress = JobProgress()
                    
                    # Re-queue the job
                    self.job_queue.put_nowait((job.priority, job.id))
                    logger.info(f"Retrying job {job_id} (attempt {job.retry_count}/{job.max_retries})")
    
    async def _execute_food_search(self, job: Job) -> Dict[str, Any]:
        """Execute a food search job"""
        job_data = job.job_data
        
        # Update progress
        with self.lock:
            job.progress.current_step = 1
            job.progress.total_steps = 4
            job.progress.step_description = "Creating search request..."
            job.progress.progress_percentage = 25.0
        
        # Convert job_data to SearchRequest
        search_request = SearchRequest(**job_data)
        
        # Update progress
        with self.lock:
            job.progress.current_step = 2
            job.progress.step_description = "Initializing browser agent..."
            job.progress.progress_percentage = 50.0
        
        # Execute the search using RappiAgent
        agent = RappiAgent()
        
        # Update progress
        with self.lock:
            job.progress.current_step = 3
            job.progress.step_description = "Searching Rappi..."
            job.progress.progress_percentage = 75.0
        
        # Run the search in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        search_response = await loop.run_in_executor(
            self.executor,
            lambda: asyncio.run(agent.search_food_options(search_request))
        )
        
        # Update progress
        with self.lock:
            job.progress.current_step = 4
            job.progress.step_description = "Processing results..."
            job.progress.progress_percentage = 100.0
        
        # Convert response to dict for storage
        return search_response.dict()
    
    async def _execute_health_check(self, job: Job) -> Dict[str, Any]:
        """Execute a health check job"""
        with self.lock:
            job.progress.step_description = "Running health check..."
            job.progress.progress_percentage = 50.0
        
        # Simple health check
        await asyncio.sleep(2)  # Simulate some work
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "message": "Browser Use system is operational"
        }


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get the global job manager instance"""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager


@asynccontextmanager
async def job_manager_lifespan():
    """Context manager for job manager lifecycle"""
    manager = get_job_manager()
    await manager.start_workers()
    try:
        yield manager
    finally:
        await manager.stop_workers()