# FastAPI Backend - API Documentation

## Overview

The FastAPI backend provides a RESTful API for CV analysis and project recommendations. It uses Celery for background task processing and supports WebSocket for real-time progress updates.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. For production, implement API key or OAuth2 authentication.

## Endpoints

### 1. Health Check

**GET** `/api/health`

Check the health status of the API and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-17T10:00:00Z",
  "services": {
    "llm": "healthy",
    "celery": "healthy",
    "cache": "healthy"
  }
}
```

---

### 2. Analyze CV

**POST** `/api/analyze`

Submit a CV and job description for analysis. Returns a job ID for tracking.

**Request:**

**Form Data:**
- `job_description` (string, required): Job description text (min 50 chars)
- `cv_file` (file, optional): CV file (PDF or DOCX)
- `cv_text` (string, optional): CV text content

**Note:** Either `cv_file` OR `cv_text` must be provided.

**Example with cURL:**
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "job_description=Senior Full Stack Developer with 5+ years experience..." \
  -F "cv_file=@/path/to/cv.pdf"
```

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "pending",
  "message": "Analysis job created successfully",
  "created_at": "2025-12-17T10:00:00Z"
}
```

---

### 3. Get Job Status

**GET** `/api/status/{job_id}`

Check the status of an analysis job.

**Parameters:**
- `job_id` (path, required): Job identifier from `/api/analyze`

**Example:**
```bash
curl "http://localhost:8000/api/status/abc123-def456-ghi789"
```

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "processing",
  "progress_percentage": 65,
  "current_step": "Generating project recommendations...",
  "created_at": "2025-12-17T10:00:00Z",
  "updated_at": "2025-12-17T10:00:45Z",
  "error": null
}
```

**Status Values:**
- `pending`: Job is queued
- `processing`: Job is being processed
- `completed`: Job finished successfully
- `failed`: Job failed with error

---

### 4. Get Results

**GET** `/api/results/{job_id}`

Retrieve the results of a completed analysis job.

**Parameters:**
- `job_id` (path, required): Job identifier

**Example:**
```bash
curl "http://localhost:8000/api/results/abc123-def456-ghi789"
```

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "completed",
  "result": {
    "skill_match_analysis": {
      "total_required_skills": 10,
      "matched_skills": ["Python", "React", "Docker"],
      "missing_required_skills": ["Kubernetes", "AWS"],
      "missing_preferred_skills": ["TypeScript"],
      "match_percentage": 70.0,
      "strengths": ["..."],
      "areas_for_improvement": ["..."]
    },
    "skill_gap_recommendations": [
      {
        "skill_gap": {
          "skill_name": "Kubernetes",
          "priority": "required",
          "category": "devops",
          "impact": "Critical for role"
        },
        "recommended_projects": [
          {
            "title": "Deploy Microservices with Kubernetes",
            "description": "...",
            "skills_covered": ["Kubernetes", "Docker"],
            "difficulty": "intermediate",
            "estimated_hours": 30,
            "key_features": ["..."],
            "learning_outcomes": ["..."]
          }
        ],
        "github_resources": [...],
        "youtube_resources": [...],
        "learning_path": "..."
      }
    ],
    "overall_assessment": "...",
    "estimated_preparation_time": "..."
  },
  "error": null
}
```

---

### 5. WebSocket Progress Updates

**WebSocket** `/api/ws/{job_id}`

Connect to receive real-time progress updates for a job.

**Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/ws/abc123-def456-ghi789');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress}% - ${data.message}`);
  
  if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
    ws.close();
  }
};
```

**Message Format:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "state": "PROCESSING",
  "progress": 65,
  "message": "Generating project recommendations..."
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "additional": "error details"
  }
}
```

**Common HTTP Status Codes:**
- `400`: Bad Request (invalid input)
- `404`: Not Found (job not found)
- `500`: Internal Server Error

---

## Python Client Example

```python
import requests
import time

# 1. Submit CV for analysis
with open('cv.pdf', 'rb') as cv_file:
    response = requests.post(
        'http://localhost:8000/api/analyze',
        data={'job_description': 'Senior Full Stack Developer...'},
        files={'cv_file': cv_file}
    )

job_data = response.json()
job_id = job_data['job_id']
print(f"Job created: {job_id}")

# 2. Poll for status
while True:
    status_response = requests.get(f'http://localhost:8000/api/status/{job_id}')
    status = status_response.json()
    
    print(f"Status: {status['status']} - {status['progress_percentage']}%")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(2)

# 3. Get results
if status['status'] == 'completed':
    results_response = requests.get(f'http://localhost:8000/api/results/{job_id}')
    results = results_response.json()
    
    print(f"Match percentage: {results['result']['skill_match_analysis']['match_percentage']}%")
    print(f"Recommendations: {len(results['result']['skill_gap_recommendations'])}")
```

---

## Rate Limiting

The API inherits rate limiting from the underlying services:
- GitHub API: 30 req/min (unauthenticated), 5000 req/hour (authenticated)
- YouTube API: 10,000 quota units/day
- OpenAI API: Based on your plan

---

## Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

These provide interactive API documentation where you can test endpoints directly.
