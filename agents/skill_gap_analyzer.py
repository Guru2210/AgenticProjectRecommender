"""Skill Gap Analyzer Agent - Identifies missing skills between CV and job requirements."""

from typing import List, Set
import difflib

from models.cv_models import CVData
from models.job_models import JobRequirements, SkillPriority
from models.recommendation_models import SkillGap, SkillMatchAnalysis
from utils.logger import get_logger
from utils.error_handler import SkillGapAnalysisError, handle_errors

logger = get_logger(__name__)


class SkillGapAnalyzerAgent:
    """Agent responsible for analyzing skill gaps between CV and job requirements."""
    
    def __init__(self):
        """Initialize skill gap analyzer agent."""
        logger.info("Skill Gap Analyzer Agent initialized")
    
    @handle_errors(raise_on_error=True)
    def analyze_gaps(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements
    ) -> SkillMatchAnalysis:
        """
        Analyze skill gaps between CV and job requirements.
        
        Args:
            cv_data: Parsed CV data
            job_requirements: Parsed job requirements
        
        Returns:
            SkillMatchAnalysis object
        
        Raises:
            SkillGapAnalysisError: If analysis fails
        """
        logger.info("Analyzing skill gaps")
        
        try:
            # Get all skills from CV (normalized)
            cv_skills = self._normalize_skills(cv_data.get_all_skill_names())
            
            # Get required and preferred skills from job (normalized)
            required_skills = self._normalize_skills(job_requirements.get_required_skill_names())
            preferred_skills = self._normalize_skills(job_requirements.get_preferred_skill_names())
            
            # Find matches and gaps
            matched_required = self._find_matches(cv_skills, required_skills)
            matched_preferred = self._find_matches(cv_skills, preferred_skills)
            
            missing_required = required_skills - matched_required
            missing_preferred = preferred_skills - matched_preferred
            
            # Calculate match percentage
            total_required = len(required_skills)
            if total_required > 0:
                match_percentage = (len(matched_required) / total_required) * 100
            else:
                match_percentage = 100.0
            
            # Identify strengths and areas for improvement
            strengths = self._identify_strengths(cv_data, job_requirements, matched_required)
            areas_for_improvement = self._identify_improvements(
                missing_required,
                missing_preferred,
                job_requirements
            )
            
            analysis = SkillMatchAnalysis(
                total_required_skills=total_required,
                matched_skills=list(matched_required | matched_preferred),
                missing_required_skills=list(missing_required),
                missing_preferred_skills=list(missing_preferred),
                match_percentage=round(match_percentage, 1),
                strengths=strengths,
                areas_for_improvement=areas_for_improvement
            )
            
            logger.info(
                f"Skill gap analysis complete: {match_percentage:.1f}% match, "
                f"{len(missing_required)} required skills missing"
            )
            
            return analysis
        
        except Exception as e:
            logger.error(f"Skill gap analysis failed: {str(e)}")
            raise SkillGapAnalysisError(
                f"Failed to analyze skill gaps: {str(e)}",
                details={"error": str(e)}
            )
    
    def get_prioritized_gaps(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements
    ) -> List[SkillGap]:
        """
        Get prioritized list of skill gaps.
        
        Args:
            cv_data: Parsed CV data
            job_requirements: Parsed job requirements
        
        Returns:
            List of SkillGap objects, sorted by priority
        """
        analysis = self.analyze_gaps(cv_data, job_requirements)
        
        gaps = []
        
        # Add required skill gaps (highest priority)
        for skill_name in analysis.missing_required_skills:
            # Find the skill requirement details
            skill_req = self._find_skill_requirement(skill_name, job_requirements.required_skills)
            
            gap = SkillGap(
                skill_name=skill_name,
                priority="required",
                category=skill_req.category.value if skill_req and skill_req.category else None,
                impact="Critical for role - this is a required skill"
            )
            gaps.append(gap)
        
        # Add preferred skill gaps (lower priority)
        for skill_name in analysis.missing_preferred_skills:
            skill_req = self._find_skill_requirement(skill_name, job_requirements.preferred_skills)
            
            gap = SkillGap(
                skill_name=skill_name,
                priority="preferred",
                category=skill_req.category.value if skill_req and skill_req.category else None,
                impact="Nice to have - would strengthen your application"
            )
            gaps.append(gap)
        
        return gaps
    
    def _normalize_skills(self, skills: List[str]) -> Set[str]:
        """
        Normalize skill names for comparison.
        
        Args:
            skills: List of skill names
        
        Returns:
            Set of normalized skill names
        """
        normalized = set()
        
        for skill in skills:
            # Convert to lowercase and strip whitespace
            normalized_skill = skill.lower().strip()
            
            # Remove common variations
            normalized_skill = normalized_skill.replace(".", "")
            normalized_skill = normalized_skill.replace("-", "")
            normalized_skill = normalized_skill.replace(" ", "")
            
            normalized.add(normalized_skill)
        
        return normalized
    
    def _find_matches(
        self,
        cv_skills: Set[str],
        job_skills: Set[str],
        similarity_threshold: float = 0.85
    ) -> Set[str]:
        """
        Find matching skills, including fuzzy matches.
        
        Args:
            cv_skills: Normalized CV skills
            job_skills: Normalized job skills
            similarity_threshold: Minimum similarity for fuzzy match
        
        Returns:
            Set of matched job skills
        """
        matches = set()
        
        for job_skill in job_skills:
            # Exact match
            if job_skill in cv_skills:
                matches.add(job_skill)
                continue
            
            # Fuzzy match
            for cv_skill in cv_skills:
                similarity = difflib.SequenceMatcher(None, job_skill, cv_skill).ratio()
                if similarity >= similarity_threshold:
                    matches.add(job_skill)
                    logger.debug(f"Fuzzy match: '{job_skill}' ~ '{cv_skill}' ({similarity:.2f})")
                    break
        
        return matches
    
    def _find_skill_requirement(self, skill_name: str, skill_requirements: List) -> any:
        """Find skill requirement by normalized name."""
        normalized_name = skill_name.lower().replace(".", "").replace("-", "").replace(" ", "")
        
        for req in skill_requirements:
            req_normalized = req.name.lower().replace(".", "").replace("-", "").replace(" ", "")
            if req_normalized == normalized_name:
                return req
        
        return None
    
    def _identify_strengths(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements,
        matched_skills: Set[str]
    ) -> List[str]:
        """Identify candidate's strengths relative to the job."""
        strengths = []
        
        if len(matched_skills) > 0:
            strengths.append(f"Possesses {len(matched_skills)} of the required/preferred skills")
        
        # Check experience level
        if cv_data.total_years_experience and job_requirements.min_years_experience:
            if cv_data.total_years_experience >= job_requirements.min_years_experience:
                strengths.append(
                    f"Meets experience requirement ({cv_data.total_years_experience} years)"
                )
        
        # Check education
        if cv_data.education and job_requirements.education_requirements:
            strengths.append("Has relevant educational background")
        
        # Check certifications
        if cv_data.certifications:
            strengths.append(f"Holds {len(cv_data.certifications)} professional certification(s)")
        
        return strengths if strengths else ["Review your CV to highlight relevant experience"]
    
    def _identify_improvements(
        self,
        missing_required: Set[str],
        missing_preferred: Set[str],
        job_requirements: JobRequirements
    ) -> List[str]:
        """Identify areas for improvement."""
        improvements = []
        
        if missing_required:
            improvements.append(
                f"Acquire {len(missing_required)} required skill(s) to meet minimum qualifications"
            )
        
        if missing_preferred:
            improvements.append(
                f"Consider learning {len(missing_preferred)} preferred skill(s) to strengthen application"
            )
        
        if not missing_required and not missing_preferred:
            improvements.append("You meet all skill requirements! Focus on showcasing your experience.")
        
        return improvements
