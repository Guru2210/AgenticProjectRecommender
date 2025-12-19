"""Request and response schemas for the FastAPI backend."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    """Response when creating a new job."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Initial job status")
    message: str = Field(..., description="Human-readable message")
    created_at: datetime = Field(..., description="Job creation timestamp")


class JobStatusResponse(BaseModel):
    """Response for job status queries."""
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current job status")
    progress_percentage: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    current_step: str = Field(..., description="Current processing step")
    created_at: datetime = Field(..., description="Job creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")


class AnalysisResultResponse(BaseModel):
    """Response containing analysis results."""
    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Job status")
    result: Optional[Dict[str, Any]] = Field(None, description="Analysis result data")
    error: Optional[str] = Field(None, description="Error message if failed")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Overall service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Check timestamp")
    services: Dict[str, str] = Field(..., description="Status of dependent services")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
