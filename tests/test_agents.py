"""Sample test file for the CV Project Recommender system."""

import pytest
from models.cv_models import CVData, Skill, Experience
from models.job_models import JobRequirements, SkillRequirement, SkillPriority
from agents.skill_gap_analyzer import SkillGapAnalyzerAgent


def test_skill_gap_analyzer():
    """Test skill gap analysis."""
    
    # Create sample CV data
    cv_data = CVData(
        name="John Doe",
        skills=[
            Skill(name="Python", category="Programming Language"),
            Skill(name="JavaScript", category="Programming Language"),
            Skill(name="React", category="Framework"),
        ],
        experience=[],
        education=[],
        certifications=[]
    )
    
    # Create sample job requirements
    job_requirements = JobRequirements(
        job_title="Full Stack Developer",
        required_skills=[
            SkillRequirement(name="Python", priority=SkillPriority.REQUIRED),
            SkillRequirement(name="React", priority=SkillPriority.REQUIRED),
            SkillRequirement(name="Node.js", priority=SkillPriority.REQUIRED),
        ],
        preferred_skills=[
            SkillRequirement(name="TypeScript", priority=SkillPriority.PREFERRED),
        ]
    )
    
    # Analyze gaps
    analyzer = SkillGapAnalyzerAgent()
    analysis = analyzer.analyze_gaps(cv_data, job_requirements)
    
    # Assertions
    assert analysis.total_required_skills == 3
    assert "nodejs" in [s.lower().replace(".", "") for s in analysis.missing_required_skills]
    assert analysis.match_percentage < 100
    assert len(analysis.matched_skills) >= 2


def test_skill_normalization():
    """Test skill name normalization."""
    
    analyzer = SkillGapAnalyzerAgent()
    
    # Test normalization
    skills = ["React.js", "Node.js", "Python 3"]
    normalized = analyzer._normalize_skills(skills)
    
    assert "reactjs" in normalized
    assert "nodejs" in normalized
    assert "python3" in normalized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
