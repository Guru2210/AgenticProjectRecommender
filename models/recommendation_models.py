"""Pydantic models for project recommendations and resources."""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from enum import Enum


class DifficultyLevel(str, Enum):
    """Project difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ResourceType(str, Enum):
    """Types of learning resources."""
    GITHUB = "github"
    YOUTUBE = "youtube"
    DOCUMENTATION = "documentation"
    TUTORIAL = "tutorial"
    COURSE = "course"


class Project(BaseModel):
    """Represents a recommended project."""
    
    title: str = Field(..., description="Project title")
    description: str = Field(..., description="Detailed project description")
    skills_covered: List[str] = Field(..., description="Skills this project will help develop")
    difficulty: DifficultyLevel = Field(..., description="Project difficulty level")
    estimated_hours: Optional[int] = Field(None, description="Estimated hours to complete")
    key_features: List[str] = Field(default_factory=list, description="Key features to implement")
    learning_outcomes: List[str] = Field(default_factory=list, description="What you'll learn")


class Resource(BaseModel):
    """Represents a learning resource (GitHub repo, YouTube video, etc.)."""
    
    type: ResourceType = Field(..., description="Type of resource")
    title: str = Field(..., description="Resource title")
    url: str = Field(..., description="Resource URL")
    description: Optional[str] = Field(None, description="Resource description")
    
    # GitHub-specific fields
    stars: Optional[int] = Field(None, description="GitHub stars")
    language: Optional[str] = Field(None, description="Primary programming language")
    last_updated: Optional[str] = Field(None, description="Last update date")
    
    # YouTube-specific fields
    channel: Optional[str] = Field(None, description="YouTube channel name")
    duration: Optional[str] = Field(None, description="Video duration")
    views: Optional[int] = Field(None, description="View count")
    
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relevance score")


class SkillGap(BaseModel):
    """Represents a skill gap identified between CV and job requirements."""
    
    skill_name: str = Field(..., description="Name of the missing skill")
    priority: str = Field(..., description="Priority level (required/preferred)")
    category: Optional[str] = Field(None, description="Skill category")
    impact: str = Field(..., description="Impact description (e.g., 'Critical for role')")


class SkillGapRecommendation(BaseModel):
    """Complete recommendation for a specific skill gap."""
    
    skill_gap: SkillGap = Field(..., description="The skill gap being addressed")
    recommended_projects: List[Project] = Field(
        default_factory=list,
        description="Recommended projects to build"
    )
    github_resources: List[Resource] = Field(
        default_factory=list,
        description="Relevant GitHub repositories"
    )
    youtube_resources: List[Resource] = Field(
        default_factory=list,
        description="Relevant YouTube tutorials"
    )
    web_resources: List[Resource] = Field(
        default_factory=list,
        description="Relevant web tutorials and learning resources"
    )
    learning_path: Optional[str] = Field(
        None,
        description="Suggested learning path/roadmap"
    )


class SkillMatchAnalysis(BaseModel):
    """Analysis of skill match between CV and job requirements."""
    
    total_required_skills: int = Field(..., description="Total number of required skills")
    matched_skills: List[str] = Field(default_factory=list, description="Skills candidate has")
    missing_required_skills: List[str] = Field(default_factory=list, description="Missing required skills")
    missing_preferred_skills: List[str] = Field(default_factory=list, description="Missing preferred skills")
    match_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall match percentage")
    
    strengths: List[str] = Field(default_factory=list, description="Candidate's strengths")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Areas to improve")


class RecommendationResult(BaseModel):
    """Complete result of the recommendation system."""
    
    skill_match_analysis: SkillMatchAnalysis = Field(..., description="Skill match analysis")
    skill_gap_recommendations: List[SkillGapRecommendation] = Field(
        default_factory=list,
        description="Recommendations for each skill gap"
    )
    overall_assessment: str = Field(..., description="Overall assessment and advice")
    estimated_preparation_time: Optional[str] = Field(
        None,
        description="Estimated time to close skill gaps"
    )
