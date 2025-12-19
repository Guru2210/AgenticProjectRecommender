"""Pydantic models for CV data structures."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class Skill(BaseModel):
    """Represents a skill extracted from a CV."""
    
    name: str = Field(..., description="Skill name (e.g., 'Python', 'React')")
    category: Optional[str] = Field(None, description="Skill category (e.g., 'Programming', 'Framework')")
    proficiency: Optional[str] = Field(None, description="Proficiency level (e.g., 'Expert', 'Intermediate')")
    years_of_experience: Optional[float] = Field(None, description="Years of experience with this skill")


class Experience(BaseModel):
    """Represents work experience from a CV."""
    
    role: str = Field(..., description="Job title/role")
    company: str = Field(..., description="Company name")
    start_date: Optional[str] = Field(None, description="Start date (flexible format)")
    end_date: Optional[str] = Field(None, description="End date or 'Present'")
    duration_months: Optional[int] = Field(None, description="Duration in months")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities")
    technologies: List[str] = Field(default_factory=list, description="Technologies used")


class Education(BaseModel):
    """Represents educational background from a CV."""
    
    degree: str = Field(..., description="Degree name (e.g., 'B.S. Computer Science')")
    institution: str = Field(..., description="University/institution name")
    graduation_year: Optional[int] = Field(None, description="Year of graduation")
    gpa: Optional[float] = Field(None, description="GPA if mentioned")
    relevant_coursework: List[str] = Field(default_factory=list, description="Relevant courses")


class Certification(BaseModel):
    """Represents certifications from a CV."""
    
    name: str = Field(..., description="Certification name")
    issuer: str = Field(..., description="Issuing organization")
    issue_date: Optional[str] = Field(None, description="Date obtained")
    expiry_date: Optional[str] = Field(None, description="Expiry date if applicable")


class CVData(BaseModel):
    """Complete structured CV data."""
    
    name: Optional[str] = Field(None, description="Candidate name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    summary: Optional[str] = Field(None, description="Professional summary")
    
    skills: List[Skill] = Field(default_factory=list, description="List of skills")
    experience: List[Experience] = Field(default_factory=list, description="Work experience")
    education: List[Education] = Field(default_factory=list, description="Educational background")
    certifications: List[Certification] = Field(default_factory=list, description="Certifications")
    
    total_years_experience: Optional[float] = Field(None, description="Total years of professional experience")
    
    def get_all_skill_names(self) -> List[str]:
        """Extract all skill names as a flat list."""
        skill_names = [skill.name for skill in self.skills]
        # Also extract skills from experience
        for exp in self.experience:
            skill_names.extend(exp.technologies)
        return list(set(skill_names))  # Remove duplicates
