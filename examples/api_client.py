"""Example Python client for the CV Project Recommender API."""

import requests
import time
from typing import Optional
from pathlib import Path


class CVRecommenderClient:
    """Client for interacting with the CV Project Recommender API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client.
        
        Args:
            base_url: Base URL of the API
        """
        self.base_url = base_url.rstrip('/')
    
    def health_check(self) -> dict:
        """
        Check API health status.
        
        Returns:
            Health status dictionary
        """
        response = requests.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()
    
    def analyze_cv(
        self,
        job_description: str,
        cv_file_path: Optional[str] = None,
        cv_text: Optional[str] = None
    ) -> str:
        """
        Submit CV for analysis.
        
        Args:
            job_description: Job description text
            cv_file_path: Path to CV file (PDF or DOCX)
            cv_text: CV text content
        
        Returns:
            Job ID for tracking
        """
        if not cv_file_path and not cv_text:
            raise ValueError("Either cv_file_path or cv_text must be provided")
        
        data = {'job_description': job_description}
        files = {}
        
        if cv_file_path:
            cv_path = Path(cv_file_path)
            if not cv_path.exists():
                raise FileNotFoundError(f"CV file not found: {cv_file_path}")
            
            files['cv_file'] = open(cv_file_path, 'rb')
        
        if cv_text:
            data['cv_text'] = cv_text
        
        try:
            response = requests.post(
                f"{self.base_url}/api/analyze",
                data=data,
                files=files
            )
            response.raise_for_status()
            
            result = response.json()
            return result['job_id']
        
        finally:
            # Close file if opened
            if files:
                files['cv_file'].close()
    
    def get_status(self, job_id: str) -> dict:
        """
        Get job status.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Status dictionary
        """
        response = requests.get(f"{self.base_url}/api/status/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def get_results(self, job_id: str) -> dict:
        """
        Get job results.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Results dictionary
        """
        response = requests.get(f"{self.base_url}/api/results/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = 2,
        timeout: int = 600,
        callback=None
    ) -> dict:
        """
        Wait for job to complete and return results.
        
        Args:
            job_id: Job identifier
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait
            callback: Optional callback function(status_dict)
        
        Returns:
            Results dictionary
        """
        start_time = time.time()
        
        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
            
            # Get status
            status = self.get_status(job_id)
            
            # Call callback if provided
            if callback:
                callback(status)
            
            # Check if completed
            if status['status'] == 'completed':
                return self.get_results(job_id)
            elif status['status'] == 'failed':
                error = status.get('error', 'Unknown error')
                raise Exception(f"Job failed: {error}")
            
            # Wait before next poll
            time.sleep(poll_interval)
    
    def analyze_and_wait(
        self,
        job_description: str,
        cv_file_path: Optional[str] = None,
        cv_text: Optional[str] = None,
        callback=None
    ) -> dict:
        """
        Submit CV and wait for results (convenience method).
        
        Args:
            job_description: Job description text
            cv_file_path: Path to CV file
            cv_text: CV text content
            callback: Optional callback for status updates
        
        Returns:
            Results dictionary
        """
        # Submit job
        job_id = self.analyze_cv(job_description, cv_file_path, cv_text)
        print(f"Job created: {job_id}")
        
        # Wait for completion
        return self.wait_for_completion(job_id, callback=callback)


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = CVRecommenderClient("http://localhost:8000")
    
    # Check health
    health = client.health_check()
    print(f"API Status: {health['status']}")
    
    # Define callback for progress updates
    def progress_callback(status):
        print(f"Progress: {status['progress_percentage']}% - {status['current_step']}")
    
    # Analyze CV
    try:
        results = client.analyze_and_wait(
            job_description="""
            Senior Full Stack Developer
            
            Requirements:
            - 5+ years experience with Python and JavaScript
            - Experience with React and Node.js
            - Knowledge of Docker and Kubernetes
            - AWS cloud experience
            
            Preferred:
            - TypeScript experience
            - CI/CD pipeline setup
            """,
            cv_file_path="sample_cv.pdf",  # Replace with actual CV path
            callback=progress_callback
        )
        
        # Print results
        print("\n=== Analysis Complete ===")
        
        analysis = results['result']['skill_match_analysis']
        print(f"\nMatch Percentage: {analysis['match_percentage']}%")
        print(f"Matched Skills: {len(analysis['matched_skills'])}")
        print(f"Missing Required Skills: {len(analysis['missing_required_skills'])}")
        
        recommendations = results['result']['skill_gap_recommendations']
        print(f"\nSkill Gap Recommendations: {len(recommendations)}")
        
        for i, rec in enumerate(recommendations[:3], 1):
            skill = rec['skill_gap']['skill_name']
            projects = len(rec['recommended_projects'])
            print(f"{i}. {skill} - {projects} project(s) recommended")
    
    except Exception as e:
        print(f"Error: {str(e)}")
