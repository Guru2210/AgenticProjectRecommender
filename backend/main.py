"""FastAPI application for CV Project Recommender backend."""

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import tempfile
import os
from pathlib import Path
from datetime import datetime
import asyncio
import json
import traceback
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.schemas import (
    JobResponse,
    JobStatusResponse,
    AnalysisResultResponse,
    HealthResponse,
    ErrorResponse,
)
from backend.job_manager import job_manager, JobStatus
from config import settings
from utils.logger import setup_logging, get_logger
from utils.guardrails import (
    input_validator,
    prompt_injection_detector,
    pii_detector,
    content_moderator,
    output_validator,
    GuardrailViolationType
)
from graph.workflow import run_workflow

# Setup logging
setup_logging(log_level=settings.log_level)
logger = get_logger(__name__)

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="CV Project Recommender API",
    description="AI-powered CV analysis and project recommendation system",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint."""
    return {
        "message": "CV Project Recommender API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "running"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns service status and dependent service checks.
    """
    from integrations.llm_client import llm_client
    
    # Check LLM API
    llm_status = "healthy"
    try:
        llm_client.validate_api_key()
    except Exception as e:
        llm_status = f"unhealthy: {str(e)}"
        logger.warning(f"LLM health check failed: {e}")
    
    overall_status = "healthy" if llm_status == "healthy" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services={
            "llm": llm_status,
            "job_manager": "healthy",
            "cache": "healthy" if settings.enable_caching else "disabled"
        }
    )


async def process_cv_analysis(job_id: str, cv_file_path: Optional[str], job_description: str):
    """
    Process CV analysis in the background.
    
    Args:
        job_id: Job identifier
        cv_file_path: Path to CV file
        job_description: Job description text
    """
    try:
        logger.info(f"Starting analysis for job {job_id}")
        job_manager.set_processing(job_id, "Parsing CV and analyzing job description...")
        
        # Run the workflow (it handles its own progress via state)
        job_manager.set_progress(job_id, 10, "Initializing workflow...")
        
        final_state = run_workflow(
            cv_file_path=cv_file_path,
            job_description=job_description
        )
        
        # Update progress from workflow state
        if final_state.get("current_step"):
            job_manager.set_progress(
                job_id, 
                final_state.get("progress_percentage", 90),
                final_state.get("current_step", "Processing...")
            )
        
        # Check for errors
        if final_state.get("errors"):
            error_msg = "; ".join(final_state["errors"])
            job_manager.set_failed(job_id, error_msg)
            logger.error(f"Job {job_id} failed with errors: {error_msg}")
            return
        
        # Get result
        if final_state.get("recommendation_result"):
            result = final_state["recommendation_result"]
            job_manager.set_completed(job_id, result.model_dump())
            logger.info(f"Job {job_id} completed successfully")
        else:
            job_manager.set_failed(job_id, "No recommendation result generated")
            logger.error(f"Job {job_id} failed: No result generated")
    
    except Exception as e:
        error_msg = f"Analysis failed: {str(e)}"
        logger.error(f"Job {job_id} exception: {error_msg}\n{traceback.format_exc()}")
        job_manager.set_failed(job_id, error_msg)
    
    finally:
        # Clean up temporary file
        if cv_file_path and os.path.exists(cv_file_path):
            try:
                os.unlink(cv_file_path)
                logger.info(f"Cleaned up temp file: {cv_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")


@app.post("/api/analyze", response_model=JobResponse)
@limiter.limit("5/hour")  # Rate limit: 5 requests per hour per IP
async def analyze_cv(
    request: Request,
    job_description: str = Form(...),
    cv_file: Optional[UploadFile] = File(None)
):
    """
    Analyze CV against job description.
    
    Upload CV file along with job description.
    Returns a job ID for tracking progress.
    
    Args:
        job_description: Job description text
        cv_file: CV file (PDF or DOCX)
    
    Returns:
        JobResponse with job_id for tracking
    """
    logger.info("Received CV analysis request")
    
    # Validate CV file is provided
    if not cv_file:
        raise HTTPException(
            status_code=400,
            detail="CV file must be provided"
        )
    
    # Guardrail 1: Validate job description
    job_desc_validation = input_validator.validate_job_description(job_description)
    if not job_desc_validation.is_valid:
        logger.warning(f"Job description validation failed: {job_desc_validation.message}")
        raise HTTPException(
            status_code=400,
            detail=job_desc_validation.message
        )
    
    # Guardrail 2: Check for prompt injection
    injection_check = prompt_injection_detector.detect(job_description)
    if not injection_check.is_valid:
        logger.warning("Prompt injection detected in job description")
        raise HTTPException(
            status_code=400,
            detail="Invalid input detected. Please review your job description."
        )
    
    # Guardrail 3: Content moderation
    content_check = content_moderator.check_content(job_description)
    if not content_check.is_valid:
        logger.warning("Inappropriate content detected in job description")
        raise HTTPException(
            status_code=400,
            detail="Inappropriate content detected. Please use professional language."
        )
    
    # Guardrail 4: Detect and mask PII in job description
    masked_job_desc, pii_matches = pii_detector.mask_pii(job_description)
    if pii_matches:
        logger.info(f"Detected and masked {len(pii_matches)} PII instances in job description")
        # Use masked version for processing
        job_description = masked_job_desc
    
    cv_file_path = None
    
    try:
        # Save uploaded file temporarily first
        file_ext = Path(cv_file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await cv_file.read()
            tmp_file.write(content)
            cv_file_path = tmp_file.name
        
        # Guardrail 5: Validate file upload
        file_validation = input_validator.validate_file_upload(
            cv_file_path,
            len(content),
            cv_file.filename
        )
        
        if not file_validation.is_valid:
            logger.warning(f"File validation failed: {file_validation.message}")
            # Clean up file
            if cv_file_path and os.path.exists(cv_file_path):
                os.unlink(cv_file_path)
            raise HTTPException(
                status_code=400,
                detail=file_validation.message
            )
        
        logger.info(f"Saved uploaded CV to: {cv_file_path}")
        
        # Create job
        job_id = job_manager.create_job()
        
        # Start background processing
        asyncio.create_task(process_cv_analysis(job_id, cv_file_path, job_description))
        
        logger.info(f"Started analysis job: {job_id}")
        
        return JobResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            message="Analysis job created successfully",
            created_at=datetime.utcnow()
        )
    
    except HTTPException:
        # Clean up file if validation failed
        if cv_file_path and os.path.exists(cv_file_path):
            try:
                os.unlink(cv_file_path)
            except:
                pass
        raise
    except Exception as e:
        logger.error(f"Failed to create analysis job: {str(e)}")
        if cv_file_path and os.path.exists(cv_file_path):
            try:
                os.unlink(cv_file_path)
            except:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create analysis job: {str(e)}"
        )


@app.get("/api/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of an analysis job.
    
    Args:
        job_id: Job identifier returned from /api/analyze
    
    Returns:
        JobStatusResponse with current status and progress
    """
    logger.debug(f"Checking status for job: {job_id}")
    
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )
    
    return JobStatusResponse(
        job_id=job_id,
        status=job.status,
        progress_percentage=job.progress_percentage,
        current_step=job.current_step,
        created_at=job.created_at,
        updated_at=job.updated_at,
        error=job.error
    )


@app.get("/api/results/{job_id}", response_model=AnalysisResultResponse)
async def get_results(job_id: str):
    """
    Get results of a completed analysis job.
    
    Args:
        job_id: Job identifier
    
    Returns:
        AnalysisResultResponse with results if completed
    """
    logger.info(f"Fetching results for job: {job_id}")
    
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )
    
    return AnalysisResultResponse(
        job_id=job_id,
        status=job.status,
        result=job.result,
        error=job.error
    )


@app.get("/api/stream/{job_id}")
async def stream_progress(job_id: str):
    """
    Server-Sent Events endpoint for real-time progress updates.
    
    Args:
        job_id: Job identifier to monitor
    
    Returns:
        StreamingResponse with SSE events
    """
    async def event_generator():
        """Generate SSE events for job progress."""
        logger.info(f"SSE stream started for job: {job_id}")
        
        try:
            while True:
                job = job_manager.get_job(job_id)
                
                if not job:
                    yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                    break
                
                event_data = {
                    "job_id": job_id,
                    "status": job.status.value,
                    "progress": job.progress_percentage,
                    "message": job.current_step,
                    "error": job.error
                }
                
                yield f"data: {json.dumps(event_data)}\n\n"
                
                # Stop streaming if job is done
                if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    logger.info(f"SSE stream ended for job: {job_id} (status: {job.status})")
                    break
                
                await asyncio.sleep(1)  # Update every second
        
        except Exception as e:
            logger.error(f"SSE stream error for job {job_id}: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="HTTPException",
            message=exc.detail,
            details=None
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"error": str(exc)}
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
