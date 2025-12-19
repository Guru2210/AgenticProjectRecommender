"""LangGraph workflow definition and creation."""

from typing import Literal
from langgraph.graph import StateGraph, END
from graph.state import WorkflowState
from graph.nodes import (
    parse_cv_node,
    analyze_job_node,
    identify_gaps_node,
    generate_recommendations_node,
    error_handler_node
)
from utils.logger import get_logger

logger = get_logger(__name__)


def should_continue(state: WorkflowState) -> Literal["continue", "error", "end"]:
    """
    Determine whether to continue the workflow or handle errors.
    
    Args:
        state: Current workflow state
    
    Returns:
        Next step: "continue", "error", or "end"
    """
    # Check for errors
    if state.get("errors") and len(state["errors"]) > 0:
        return "error"
    
    # Check if we have final results
    if state.get("recommendation_result"):
        return "end"
    
    return "continue"


def create_workflow():
    """
    Create and compile the LangGraph workflow.
    
    Returns:
        Compiled workflow graph
    """
    logger.info("Creating LangGraph workflow")
    
    # Create the state graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("parse_cv", parse_cv_node)
    workflow.add_node("analyze_job", analyze_job_node)
    workflow.add_node("identify_gaps", identify_gaps_node)
    workflow.add_node("generate_recommendations", generate_recommendations_node)
    workflow.add_node("error_handler", error_handler_node)
    
    # Set entry point
    workflow.set_entry_point("parse_cv")
    
    # Add edges
    # parse_cv -> analyze_job
    workflow.add_conditional_edges(
        "parse_cv",
        should_continue,
        {
            "continue": "analyze_job",
            "error": "error_handler",
            "end": END
        }
    )
    
    # analyze_job -> identify_gaps
    workflow.add_conditional_edges(
        "analyze_job",
        should_continue,
        {
            "continue": "identify_gaps",
            "error": "error_handler",
            "end": END
        }
    )
    
    # identify_gaps -> generate_recommendations
    workflow.add_conditional_edges(
        "identify_gaps",
        should_continue,
        {
            "continue": "generate_recommendations",
            "error": "error_handler",
            "end": END
        }
    )
    
    # generate_recommendations -> END
    workflow.add_conditional_edges(
        "generate_recommendations",
        should_continue,
        {
            "continue": END,
            "error": "error_handler",
            "end": END
        }
    )
    
    # error_handler -> END
    workflow.add_edge("error_handler", END)
    
    # Compile the graph
    app = workflow.compile()
    
    logger.info("LangGraph workflow created successfully")
    
    return app


def run_workflow(cv_file_path: str = None, cv_text: str = None, job_description: str = None):
    """
    Run the complete workflow.
    
    Args:
        cv_file_path: Path to CV file (optional if cv_text provided)
        cv_text: CV text content (optional if cv_file_path provided)
        job_description: Job description text
    
    Returns:
        Final workflow state
    """
    logger.info("Starting workflow execution")
    
    # Create workflow
    app = create_workflow()
    
    # Initialize state
    initial_state = {
        "cv_file_path": cv_file_path,
        "cv_text": cv_text,
        "job_description": job_description,
        "cv_data": None,
        "job_requirements": None,
        "skill_match_analysis": None,
        "skill_gap_recommendations": None,
        "recommendation_result": None,
        "errors": [],
        "current_step": "Starting...",
        "progress_percentage": 0
    }
    
    # Run workflow
    try:
        final_state = app.invoke(initial_state)
        logger.info("Workflow execution completed")
        return final_state
    
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        initial_state["errors"].append(str(e))
        initial_state["current_step"] = "Failed"
        return initial_state
