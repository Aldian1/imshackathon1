"""
Job system API endpoints
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from datetime import datetime

from app.models import (
    JobRequest, JobResponse, JobListResponse, Job, JobStatus, JobType,
    SearchRequest, ErrorResponse
)
from app.jobs import get_job_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, summary="Create a new job")
async def create_job(job_request: JobRequest) -> JobResponse:
    """
    Create a new async job for Browser Use tasks
    
    ## Job Types:
    - **food_search**: Search for food on Rappi (job_data should contain SearchRequest fields)
    - **health_check**: Simple health check test
    
    ## Example for food search:
    ```json
    {
        "job_type": "food_search",
        "job_data": {
            "location": "Buenos Aires, Argentina",
            "food_types": ["pizza", "sushi"],
            "price_range": "medium",
            "delivery_time": 30
        },
        "priority": 5,
        "timeout_seconds": 300
    }
    ```
    
    Returns immediately with job ID for status polling.
    """
    try:
        job_manager = get_job_manager()
        job = job_manager.create_job(job_request)
        
        return JobResponse(
            job_id=job.id,
            status=job.status,
            message="Job created successfully",
            created_at=job.created_at,
            estimated_completion=datetime.now().replace(second=0, microsecond=0) + 
                              job_request.timeout_seconds * 0.8  # Estimate 80% of timeout
        )
        
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobResponse, summary="Get job status")
async def get_job_status(job_id: str) -> JobResponse:
    """
    Get the current status and results of a job
    
    ## Response includes:
    - **status**: pending, running, completed, failed, cancelled
    - **progress**: Current progress information (if running)
    - **result**: Job results (if completed)
    - **error_message**: Error details (if failed)
    
    ## Status Meanings:
    - `pending`: Job is queued waiting to be processed
    - `running`: Job is currently being executed
    - `completed`: Job finished successfully with results
    - `failed`: Job failed with error message
    - `cancelled`: Job was cancelled before execution
    """
    job_manager = get_job_manager()
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Create response based on job status
    response_data = {
        "job_id": job.id,
        "status": job.status,
        "created_at": job.created_at
    }
    
    if job.status == JobStatus.PENDING:
        response_data["message"] = "Job is queued for processing"
        
    elif job.status == JobStatus.RUNNING:
        response_data["message"] = f"Job is running: {job.progress.step_description}"
        response_data["progress"] = job.progress
        
    elif job.status == JobStatus.COMPLETED:
        response_data["message"] = "Job completed successfully"
        response_data["result"] = job.result
        
    elif job.status == JobStatus.FAILED:
        response_data["message"] = f"Job failed: {job.error_message}"
        response_data["error_message"] = job.error_message
        
    elif job.status == JobStatus.CANCELLED:
        response_data["message"] = "Job was cancelled"
    
    return JobResponse(**response_data)


@router.get("/jobs", response_model=JobListResponse, summary="List jobs")
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of jobs to return"),
    page: int = Query(1, ge=1, description="Page number (starting from 1)")
) -> JobListResponse:
    """
    List jobs with optional filtering
    
    ## Query Parameters:
    - **status**: Filter by job status (pending, running, completed, failed, cancelled)
    - **limit**: Number of jobs per page (1-100)
    - **page**: Page number for pagination
    
    Returns jobs sorted by creation time (newest first).
    """
    job_manager = get_job_manager()
    
    # Calculate offset for pagination
    offset = (page - 1) * limit
    
    # Get all jobs matching criteria
    all_jobs = job_manager.list_jobs(status=status, limit=1000)  # Get all matching
    total_count = len(all_jobs)
    
    # Apply pagination
    jobs_page = all_jobs[offset:offset + limit]
    
    # Convert to response format
    job_responses = []
    for job in jobs_page:
        job_response = {
            "job_id": job.id,
            "status": job.status,
            "created_at": job.created_at
        }
        
        if job.status == JobStatus.PENDING:
            job_response["message"] = "Queued for processing"
        elif job.status == JobStatus.RUNNING:
            job_response["message"] = f"Running: {job.progress.step_description}"
            job_response["progress"] = job.progress
        elif job.status == JobStatus.COMPLETED:
            job_response["message"] = "Completed successfully"
            job_response["result"] = job.result
        elif job.status == JobStatus.FAILED:
            job_response["message"] = f"Failed: {job.error_message}"
            job_response["error_message"] = job.error_message
        elif job.status == JobStatus.CANCELLED:
            job_response["message"] = "Cancelled"
        
        job_responses.append(JobResponse(**job_response))
    
    return JobListResponse(
        jobs=job_responses,
        total_count=total_count,
        page=page,
        page_size=limit
    )


@router.delete("/jobs/{job_id}", summary="Cancel job")
async def cancel_job(job_id: str) -> dict:
    """
    Cancel a pending job
    
    Only jobs with status 'pending' can be cancelled.
    Jobs that are already running will continue to completion.
    """
    job_manager = get_job_manager()
    
    if job_manager.cancel_job(job_id):
        return {"message": f"Job {job_id} cancelled successfully"}
    else:
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel job in status: {job.status}"
            )


@router.post("/jobs/food-search", response_model=JobResponse, summary="Create food search job")
async def create_food_search_job(search_request: SearchRequest) -> JobResponse:
    """
    Convenience endpoint to create a food search job
    
    This is equivalent to POST /jobs with job_type="food_search" 
    but provides a cleaner interface for food searches.
    """
    job_request = JobRequest(
        job_type=JobType.FOOD_SEARCH,
        job_data=search_request.dict(),
        priority=5,
        timeout_seconds=300
    )
    
    return await create_job(job_request)


@router.get("/jobs/stats", summary="Get job statistics")
async def get_job_stats() -> dict:
    """
    Get statistics about jobs in the system
    """
    job_manager = get_job_manager()
    
    all_jobs = job_manager.list_jobs(limit=1000)
    
    stats = {
        "total_jobs": len(all_jobs),
        "pending": len([j for j in all_jobs if j.status == JobStatus.PENDING]),
        "running": len([j for j in all_jobs if j.status == JobStatus.RUNNING]),
        "completed": len([j for j in all_jobs if j.status == JobStatus.COMPLETED]),
        "failed": len([j for j in all_jobs if j.status == JobStatus.FAILED]),
        "cancelled": len([j for j in all_jobs if j.status == JobStatus.CANCELLED]),
    }
    
    return stats