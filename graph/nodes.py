"""Node implementations for the LangGraph workflow."""

from typing import Dict, Any
from agents.cv_parser import CVParserAgent
from agents.job_analyzer import JobAnalyzerAgent
from agents.skill_gap_analyzer import SkillGapAnalyzerAgent
from agents.project_recommender import ProjectRecommenderAgent
from utils.logger import get_logger
from utils.error_handler import format_error_for_user

logger = get_logger(__name__)

# Initialize agents
cv_parser = CVParserAgent()
job_analyzer = JobAnalyzerAgent()
skill_gap_analyzer = SkillGapAnalyzerAgent()
project_recommender = ProjectRecommenderAgent()


def parse_cv_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse CV and extract structured data.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state
    """
    logger.info("Executing parse_cv_node")
    
    try:
        state["current_step"] = "Parsing CV..."
        state["progress_percentage"] = 10
        
        # Parse CV from file or text
        if state.get("cv_file_path"):
            cv_data = cv_parser.parse_cv(state["cv_file_path"])
        elif state.get("cv_text"):
            cv_data = cv_parser.parse_cv_text(state["cv_text"])
        else:
            raise ValueError("No CV file path or text provided")
        
        state["cv_data"] = cv_data
        state["progress_percentage"] = 25
        
        logger.info("CV parsing completed successfully")
        
    except Exception as e:
        error_msg = format_error_for_user(e)
        logger.error(f"CV parsing failed: {error_msg}")
        state["errors"].append(error_msg)
    
    return state


def analyze_job_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze job description and extract requirements.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state
    """
    logger.info("Executing analyze_job_node")
    
    try:
        state["current_step"] = "Analyzing job description..."
        state["progress_percentage"] = 30
        
        job_requirements = job_analyzer.analyze_job(state["job_description"])
        
        state["job_requirements"] = job_requirements
        state["progress_percentage"] = 45
        
        logger.info("Job analysis completed successfully")
        
    except Exception as e:
        error_msg = format_error_for_user(e)
        logger.error(f"Job analysis failed: {error_msg}")
        state["errors"].append(error_msg)
    
    return state


def identify_gaps_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify skill gaps between CV and job requirements.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state
    """
    logger.info("Executing identify_gaps_node")
    
    try:
        state["current_step"] = "Identifying skill gaps..."
        state["progress_percentage"] = 50
        
        # Check if we have required data
        if not state.get("cv_data") or not state.get("job_requirements"):
            raise ValueError("Missing CV data or job requirements")
        
        skill_match_analysis = skill_gap_analyzer.analyze_gaps(
            state["cv_data"],
            state["job_requirements"]
        )
        
        state["skill_match_analysis"] = skill_match_analysis
        state["progress_percentage"] = 60
        
        logger.info("Skill gap analysis completed successfully")
        
    except Exception as e:
        error_msg = format_error_for_user(e)
        logger.error(f"Skill gap analysis failed: {error_msg}")
        state["errors"].append(error_msg)
    
    return state


def generate_recommendations_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate project recommendations and find learning resources.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state
    """
    logger.info("Executing generate_recommendations_node")
    
    try:
        state["current_step"] = "Generating project recommendations..."
        state["progress_percentage"] = 65
        
        # Check if we have required data
        if not state.get("cv_data") or not state.get("job_requirements"):
            raise ValueError("Missing CV data or job requirements")
        
        recommendation_result = project_recommender.generate_recommendations(
            state["cv_data"],
            state["job_requirements"]
        )
        
        state["recommendation_result"] = recommendation_result
        state["skill_gap_recommendations"] = recommendation_result.skill_gap_recommendations
        state["current_step"] = "Complete!"
        state["progress_percentage"] = 100
        
        logger.info("Recommendations generated successfully")
        
    except Exception as e:
        error_msg = format_error_for_user(e)
        logger.error(f"Recommendation generation failed: {error_msg}")
        state["errors"].append(error_msg)
    
    return state


def error_handler_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle errors in the workflow.
    
    Args:
        state: Current workflow state
    
    Returns:
        Updated state
    """
    logger.info("Executing error_handler_node")
    
    state["current_step"] = "Error occurred"
    state["progress_percentage"] = 0
    
    # Log all errors
    for error in state.get("errors", []):
        logger.error(f"Workflow error: {error}")
    
    return state
