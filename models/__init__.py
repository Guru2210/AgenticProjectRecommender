"""Data models for the CV Project Recommender system."""

from .cv_models import Skill, Experience, Education, CVData
from .job_models import SkillRequirement, JobRequirements
from .recommendation_models import Project, Resource, SkillGapRecommendation, RecommendationResult

__all__ = [
    "Skill",
    "Experience",
    "Education",
    "CVData",
    "SkillRequirement",
    "JobRequirements",
    "Project",
    "Resource",
    "SkillGapRecommendation",
    "RecommendationResult",
]
