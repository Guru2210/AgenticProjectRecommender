"""
In-memory job manager for CV analysis tasks.
Provides thread-safe job state management without external dependencies.
"""

import threading
import time
from typing import Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import uuid

from utils.logger import get_logger

logger = get_logger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobState:
    """Represents the state of a job."""
    job_id: str
    status: JobStatus
    progress_percentage: int = 0
    current_step: str = "Initializing..."
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def update(self, **kwargs):
        """Update job state fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()


class JobManager:
    """
    Thread-safe in-memory job manager.
    Stores job states and provides progress tracking.
    """
    
    def __init__(self, retention_seconds: int = 3600):
        """
        Initialize job manager.
        
        Args:
            retention_seconds: How long to keep completed jobs (default 1 hour)
        """
        self._jobs: Dict[str, JobState] = {}
        self._lock = threading.Lock()
        self._retention_seconds = retention_seconds
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread to clean up old jobs."""
        def cleanup_loop():
            while True:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_old_jobs()
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info("Job cleanup thread started")
    
    def _cleanup_old_jobs(self):
        """Remove jobs older than retention period."""
        with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(seconds=self._retention_seconds)
            jobs_to_remove = [
                job_id for job_id, job in self._jobs.items()
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
                and job.updated_at < cutoff_time
            ]
            
            for job_id in jobs_to_remove:
                del self._jobs[job_id]
                logger.info(f"Cleaned up old job: {job_id}")
            
            if jobs_to_remove:
                logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
    
    def create_job(self) -> str:
        """
        Create a new job and return its ID.
        
        Returns:
            Job ID (UUID)
        """
        job_id = str(uuid.uuid4())
        
        with self._lock:
            self._jobs[job_id] = JobState(
                job_id=job_id,
                status=JobStatus.PENDING
            )
        
        logger.info(f"Created job: {job_id}")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[JobState]:
        """
        Get job state by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            JobState or None if not found
        """
        with self._lock:
            return self._jobs.get(job_id)
    
    def update_job(self, job_id: str, **kwargs):
        """
        Update job state.
        
        Args:
            job_id: Job identifier
            **kwargs: Fields to update (status, progress_percentage, current_step, etc.)
        """
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].update(**kwargs)
                logger.debug(f"Updated job {job_id}: {kwargs}")
    
    def set_processing(self, job_id: str, current_step: str = "Processing..."):
        """Mark job as processing."""
        self.update_job(
            job_id,
            status=JobStatus.PROCESSING,
            current_step=current_step
        )
    
    def set_progress(self, job_id: str, percentage: int, step: str):
        """Update job progress."""
        self.update_job(
            job_id,
            progress_percentage=min(100, max(0, percentage)),
            current_step=step
        )
    
    def set_completed(self, job_id: str, result: Any):
        """Mark job as completed with result."""
        self.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress_percentage=100,
            current_step="Completed",
            result=result
        )
        logger.info(f"Job completed: {job_id}")
    
    def set_failed(self, job_id: str, error: str):
        """Mark job as failed with error."""
        self.update_job(
            job_id,
            status=JobStatus.FAILED,
            current_step="Failed",
            error=error
        )
        logger.error(f"Job failed: {job_id} - {error}")
    
    def create_progress_callback(self, job_id: str) -> Callable[[int, str], None]:
        """
        Create a progress callback function for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Callback function that accepts (percentage, step_description)
        """
        def callback(percentage: int, step: str):
            self.set_progress(job_id, percentage, step)
        
        return callback
    
    def get_all_jobs(self) -> Dict[str, JobState]:
        """Get all jobs (for debugging/monitoring)."""
        with self._lock:
            return self._jobs.copy()
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                logger.info(f"Deleted job: {job_id}")
                return True
            return False


# Global job manager instance
job_manager = JobManager(retention_seconds=3600)
