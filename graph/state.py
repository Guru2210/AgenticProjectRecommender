"""State definition for the LangGraph workflow."""

from typing import TypedDict, Optional, List
from models.cv_models import CVData
from models.job_models import JobRequirements
from models.recommendation_models import SkillMatchAnalysis, SkillGapRecommendation, RecommendationResult


class WorkflowState(TypedDict):
    """State schema for the recommendation workflow."""
    
    # Input data
    cv_file_path: Optional[str]
    cv_text: Optional[str]
    job_description: str
    
    # Parsed data
    cv_data: Optional[CVData]
    job_requirements: Optional[JobRequirements]
    
    # Analysis results
    skill_match_analysis: Optional[SkillMatchAnalysis]
    skill_gap_recommendations: Optional[List[SkillGapRecommendation]]
    
    # Final result
    recommendation_result: Optional[RecommendationResult]
    
    # Error tracking
    errors: List[str]
    
    # Progress tracking
    current_step: str
    progress_percentage: int
