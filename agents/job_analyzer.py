"""Job Analyzer Agent - Analyzes job descriptions and extracts requirements."""

import json
from typing import List

from models.job_models import JobRequirements, SkillRequirement, SkillPriority
from integrations.llm_client import llm_client
from utils.logger import get_logger
from utils.error_handler import JobAnalysisError, handle_errors

logger = get_logger(__name__)


class JobAnalyzerAgent:
    """Agent responsible for analyzing job descriptions and extracting requirements."""
    
    def __init__(self):
        """Initialize job analyzer agent."""
        self.llm = llm_client
        logger.info("Job Analyzer Agent initialized")
    
    @handle_errors(raise_on_error=True)
    def analyze_job(self, job_description: str) -> JobRequirements:
        """
        Analyze a job description and extract structured requirements.
        
        Args:
            job_description: Job description text
        
        Returns:
            JobRequirements object
        
        Raises:
            JobAnalysisError: If analysis fails
        """
        logger.info("Analyzing job description")
        
        if not job_description or len(job_description.strip()) < 50:
            raise JobAnalysisError(
                "Job description is too short or empty",
                details={"text_length": len(job_description)}
            )
        
        # Use LLM to extract structured requirements
        job_requirements = self._extract_requirements(job_description)
        
        logger.info(
            f"Successfully analyzed job: {len(job_requirements.required_skills)} required skills, "
            f"{len(job_requirements.preferred_skills)} preferred skills"
        )
        
        return job_requirements
    
    def _extract_requirements(self, job_description: str) -> JobRequirements:
        """
        Use LLM to extract structured requirements from job description.
        
        Args:
            job_description: Job description text
        
        Returns:
            JobRequirements object
        """
        system_message = """You are an expert job description analyzer. Extract structured requirements from the job posting.
Your response must be valid JSON matching this schema:
{
  "job_title": "string",
  "company": "string or null",
  "required_skills": [
    {
      "name": "string",
      "priority": "required",
      "category": "programming_language|framework|database|cloud|devops|frontend|backend|mobile|data_science|soft_skill|other or null",
      "years_required": number or null,
      "description": "string or null"
    }
  ],
  "preferred_skills": [
    {
      "name": "string",
      "priority": "preferred",
      "category": "programming_language|framework|database|cloud|devops|frontend|backend|mobile|data_science|soft_skill|other or null",
      "years_required": number or null,
      "description": "string or null"
    }
  ],
  "min_years_experience": number or null,
  "education_requirements": ["string"],
  "responsibilities": ["string"]
}

Carefully distinguish between required (must-have) and preferred (nice-to-have) skills.
Categorize each skill appropriately. Extract years of experience if mentioned."""
        
        prompt = f"""Analyze the following job description and extract structured requirements:

{job_description}

Return ONLY valid JSON, no additional text."""
        
        try:
            response = self.llm.generate_structured(
                prompt=prompt,
                system_message=system_message,
                response_format="json"
            )
            
            # Clean response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            # Parse JSON
            data = json.loads(response)
            
            # Convert to Pydantic model
            job_requirements = JobRequirements(**data)
            
            return job_requirements
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.debug(f"LLM response: {response[:500]}")
            raise JobAnalysisError(
                "Failed to parse job requirements from LLM response",
                details={"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Failed to extract job requirements: {str(e)}")
            raise JobAnalysisError(
                f"Failed to extract job requirements: {str(e)}",
                details={"error": str(e)}
            )
    
    def extract_key_skills(self, job_description: str) -> List[str]:
        """
        Quick extraction of key skills from job description.
        
        Args:
            job_description: Job description text
        
        Returns:
            List of skill names
        """
        job_requirements = self.analyze_job(job_description)
        return job_requirements.get_all_skill_names()
