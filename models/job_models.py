"""Pydantic models for job description data structures."""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class SkillPriority(str, Enum):
    """Priority level for a skill requirement."""
    REQUIRED = "required"
    PREFERRED = "preferred"
    NICE_TO_HAVE = "nice_to_have"


class SkillCategory(str, Enum):
    """Categories for organizing skills."""
    PROGRAMMING_LANGUAGE = "programming_language"
    FRAMEWORK = "framework"
    DATABASE = "database"
    CLOUD = "cloud"
    DEVOPS = "devops"
    FRONTEND = "frontend"
    BACKEND = "backend"
    MOBILE = "mobile"
    DATA_SCIENCE = "data_science"
    SOFT_SKILL = "soft_skill"
    OTHER = "other"


class SkillRequirement(BaseModel):
    """Represents a skill requirement from a job description."""
    
    name: str = Field(..., description="Skill name")
    priority: SkillPriority = Field(..., description="Priority level")
    category: Optional[SkillCategory] = Field(None, description="Skill category")
    years_required: Optional[int] = Field(None, description="Years of experience required")
    description: Optional[str] = Field(None, description="Additional context about the requirement")


class JobRequirements(BaseModel):
    """Complete structured job requirements data."""
    
    job_title: str = Field(..., description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    
    required_skills: List[SkillRequirement] = Field(
        default_factory=list,
        description="Must-have skills"
    )
    preferred_skills: List[SkillRequirement] = Field(
        default_factory=list,
        description="Nice-to-have skills"
    )
    
    min_years_experience: Optional[int] = Field(None, description="Minimum years of experience")
    education_requirements: List[str] = Field(
        default_factory=list,
        description="Education requirements"
    )
    
    responsibilities: List[str] = Field(
        default_factory=list,
        description="Key responsibilities"
    )
    
    def get_all_skill_names(self) -> List[str]:
        """Extract all required and preferred skill names."""
        skills = []
        for skill in self.required_skills + self.preferred_skills:
            skills.append(skill.name)
        return skills
    
    def get_required_skill_names(self) -> List[str]:
        """Extract only required skill names."""
        return [skill.name for skill in self.required_skills]
    
    def get_preferred_skill_names(self) -> List[str]:
        """Extract only preferred skill names."""
        return [skill.name for skill in self.preferred_skills]
