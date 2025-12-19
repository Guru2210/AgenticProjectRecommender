"""Project Recommender Agent - Generates project recommendations and finds learning resources."""

import json
from typing import List

from models.cv_models import CVData
from models.job_models import JobRequirements
from models.recommendation_models import (
    SkillGap,
    SkillGapRecommendation,
    Project,
    DifficultyLevel,
    RecommendationResult
)
from integrations.llm_client import llm_client
from integrations.github_search import GitHubSearchClient
from integrations.youtube_search import YouTubeSearchClient
from integrations.google_search import google_search_client
from agents.skill_gap_analyzer import SkillGapAnalyzerAgent
from utils.logger import get_logger
from utils.error_handler import ProjectRecommendationError, handle_errors

logger = get_logger(__name__)


class ProjectRecommenderAgent:
    """Agent responsible for generating project recommendations and finding learning resources."""
    
    def __init__(self):
        """Initialize project recommender agent."""
        self.llm = llm_client
        self.github_client = GitHubSearchClient()
        self.youtube_client = YouTubeSearchClient()
        self.google_client = google_search_client
        self.skill_gap_analyzer = SkillGapAnalyzerAgent()
        logger.info("Project Recommender Agent initialized")
    
    @handle_errors(raise_on_error=True)
    def generate_recommendations(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements
    ) -> RecommendationResult:
        """
        Generate complete recommendations for skill gaps.
        
        Args:
            cv_data: Parsed CV data
            job_requirements: Parsed job requirements
        
        Returns:
            RecommendationResult object
        
        Raises:
            ProjectRecommendationError: If recommendation generation fails
        """
        logger.info("Generating project recommendations")
        
        try:
            # Analyze skill gaps
            skill_match_analysis = self.skill_gap_analyzer.analyze_gaps(cv_data, job_requirements)
            skill_gaps = self.skill_gap_analyzer.get_prioritized_gaps(cv_data, job_requirements)
            
            # Generate recommendations for each skill gap
            recommendations = []
            
            for skill_gap in skill_gaps[:10]:  # Limit to top 10 gaps
                logger.info(f"Generating recommendations for skill: {skill_gap.skill_name}")
                
                recommendation = self._generate_skill_recommendation(skill_gap)
                recommendations.append(recommendation)
            
            # Generate overall assessment
            overall_assessment = self._generate_overall_assessment(
                cv_data,
                job_requirements,
                skill_match_analysis,
                recommendations
            )
            
            # Estimate preparation time
            prep_time = self._estimate_preparation_time(recommendations)
            
            result = RecommendationResult(
                skill_match_analysis=skill_match_analysis,
                skill_gap_recommendations=recommendations,
                overall_assessment=overall_assessment,
                estimated_preparation_time=prep_time
            )
            
            logger.info(f"Generated {len(recommendations)} skill gap recommendations")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {str(e)}")
            raise ProjectRecommendationError(
                f"Failed to generate recommendations: {str(e)}",
                details={"error": str(e)}
            )
    
    def _generate_skill_recommendation(self, skill_gap: SkillGap) -> SkillGapRecommendation:
        """
        Generate recommendation for a single skill gap.
        
        Args:
            skill_gap: SkillGap object
        
        Returns:
            SkillGapRecommendation object
        """
        # Generate project ideas using LLM
        projects = self._generate_project_ideas(skill_gap)
        
        # Search for GitHub resources
        github_resources = self._search_github_resources(skill_gap)
        
        # Search for YouTube tutorials
        youtube_resources = self._search_youtube_resources(skill_gap)
        
        # Search for web resources
        web_resources = self._search_web_resources(skill_gap)
        
        # Generate learning path
        learning_path = self._generate_learning_path(skill_gap, projects)
        
        return SkillGapRecommendation(
            skill_gap=skill_gap,
            recommended_projects=projects,
            github_resources=github_resources,
            youtube_resources=youtube_resources,
            web_resources=web_resources,
            learning_path=learning_path
        )
    
    def _generate_project_ideas(self, skill_gap: SkillGap) -> List[Project]:
        """Generate project ideas for a skill using LLM."""
        system_message = """You are an expert software engineering mentor. Generate practical project ideas to help someone learn a specific skill.
Your response must be valid JSON matching this schema:
{
  "projects": [
    {
      "title": "string",
      "description": "string",
      "skills_covered": ["string"],
      "difficulty": "beginner|intermediate|advanced",
      "estimated_hours": number,
      "key_features": ["string"],
      "learning_outcomes": ["string"]
    }
  ]
}

Generate 3 projects: one beginner, one intermediate, and one advanced.
Make them practical, hands-on, and portfolio-worthy."""
        
        prompt = f"""Generate 3 project ideas to learn {skill_gap.skill_name}.

Skill: {skill_gap.skill_name}
Category: {skill_gap.category or 'General'}
Priority: {skill_gap.priority}

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
            
            # Convert to Project objects
            projects = [Project(**project_data) for project_data in data.get("projects", [])]
            
            return projects
        
        except Exception as e:
            logger.warning(f"Failed to generate project ideas for {skill_gap.skill_name}: {str(e)}")
            # Return a default project
            return [
                Project(
                    title=f"Learn {skill_gap.skill_name}",
                    description=f"A hands-on project to learn {skill_gap.skill_name}",
                    skills_covered=[skill_gap.skill_name],
                    difficulty=DifficultyLevel.BEGINNER,
                    estimated_hours=20,
                    key_features=["Core concepts", "Practical application"],
                    learning_outcomes=[f"Understand {skill_gap.skill_name} fundamentals"]
                )
            ]
    
    def _search_github_resources(self, skill_gap: SkillGap) -> List:
        """Search for GitHub resources for a skill."""
        try:
            # Search for project examples
            resources = self.github_client.search_project_examples(
                skill=skill_gap.skill_name,
                difficulty="beginner",
                max_results=3
            )
            
            return resources
        
        except Exception as e:
            logger.warning(f"Failed to search GitHub for {skill_gap.skill_name}: {str(e)}")
            return []
    
    def _search_youtube_resources(self, skill_gap: SkillGap) -> List:
        """Search for YouTube tutorials for a skill."""
        try:
            # Search for tutorials
            resources = self.youtube_client.search_tutorials(
                skill=skill_gap.skill_name,
                difficulty="beginner",
                max_results=3
            )
            
            return resources
        
        except Exception as e:
            logger.warning(f"Failed to search YouTube for {skill_gap.skill_name}: {str(e)}")
            return []
    
    def _search_web_resources(self, skill_gap: SkillGap) -> List:
        """Search for web tutorials and learning resources for a skill."""
        try:
            # Search for learning resources
            resources = self.google_client.search_learning_resources(
                skill=skill_gap.skill_name,
                max_results=3
            )
            
            return resources
        
        except Exception as e:
            logger.warning(f"Failed to search web for {skill_gap.skill_name}: {str(e)}")
            return []
    
    def _generate_learning_path(self, skill_gap: SkillGap, projects: List[Project]) -> str:
        """Generate a learning path for a skill."""
        system_message = """You are an expert learning advisor. Create a concise, actionable learning path for acquiring a specific skill.

IMPORTANT: Format your response as plain text with clear structure. Use simple numbering (1., 2., 3.) for steps. 
Do NOT use markdown formatting (no **, ##, ###, or other markdown symbols).
Use simple line breaks and indentation for readability."""
        
        project_titles = [p.title for p in projects]
        
        prompt = f"""Create a brief learning path (3-5 steps) for learning {skill_gap.skill_name}.

Skill: {skill_gap.skill_name}
Priority: {skill_gap.priority}
Recommended Projects: {', '.join(project_titles)}

Format your response as a numbered list with clear, actionable steps.
Each step should be 1-2 sentences maximum.
Do NOT use markdown formatting (**, ##, etc.) - use plain text only.
Keep it concise (max 200 words)."""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7
            )
            
            return response.strip()
        
        except Exception as e:
            logger.warning(f"Failed to generate learning path for {skill_gap.skill_name}: {str(e)}")
            return f"1. Learn {skill_gap.skill_name} fundamentals\n2. Build practice projects\n3. Apply to real-world scenarios"
    
    def _generate_overall_assessment(
        self,
        cv_data: CVData,
        job_requirements: JobRequirements,
        skill_match_analysis,
        recommendations: List[SkillGapRecommendation]
    ) -> str:
        """Generate overall assessment and advice."""
        system_message = """You are a career advisor. Provide an encouraging, actionable assessment of a candidate's readiness for a job.

IMPORTANT: Format your response as plain text. Do NOT use markdown formatting (no **, ##, ###, or other markdown symbols).
Use clear section headers followed by colons and organize content with simple numbering or bullet points using hyphens (-)."""
        
        prompt = f"""Provide an overall assessment for a candidate applying to: {job_requirements.job_title}

Match Percentage: {skill_match_analysis.match_percentage}%
Matched Skills: {len(skill_match_analysis.matched_skills)}
Missing Required Skills: {len(skill_match_analysis.missing_required_skills)}
Missing Preferred Skills: {len(skill_match_analysis.missing_preferred_skills)}

Strengths:
{chr(10).join('- ' + s for s in skill_match_analysis.strengths)}

Areas for Improvement:
{chr(10).join('- ' + a for a in skill_match_analysis.areas_for_improvement)}

Provide:
1. Overall readiness assessment
2. Key recommendations (2-3 points)
3. Encouragement and next steps

IMPORTANT: Use plain text only. Do NOT use markdown formatting (**, ##, etc.).
Use section headers followed by colons (e.g., "Overall Readiness:" or "Key Recommendations:").
Keep it concise (max 250 words) and actionable."""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_message=system_message,
                temperature=0.7
            )
            
            return response.strip()
        
        except Exception as e:
            logger.warning(f"Failed to generate overall assessment: {str(e)}")
            
            # Fallback assessment
            if skill_match_analysis.match_percentage >= 80:
                return "You're well-qualified for this role! Focus on highlighting your relevant experience and consider learning the remaining skills to strengthen your application."
            elif skill_match_analysis.match_percentage >= 60:
                return "You have a solid foundation for this role. Focus on acquiring the missing required skills through the recommended projects to improve your candidacy."
            else:
                return "This role requires significant skill development. Focus on the required skills first, starting with the beginner projects. With dedicated effort, you can build the necessary expertise."
    
    def _estimate_preparation_time(self, recommendations: List[SkillGapRecommendation]) -> str:
        """Estimate time needed to close skill gaps."""
        total_hours = 0
        
        for rec in recommendations:
            # Take the beginner project time estimate
            if rec.recommended_projects:
                beginner_projects = [p for p in rec.recommended_projects if p.difficulty == DifficultyLevel.BEGINNER]
                if beginner_projects:
                    total_hours += beginner_projects[0].estimated_hours or 20
                else:
                    total_hours += rec.recommended_projects[0].estimated_hours or 20
        
        # Convert to weeks (assuming 10 hours per week)
        weeks = total_hours / 10
        
        if weeks < 4:
            return f"Approximately {int(weeks)} weeks with consistent practice (10 hours/week)"
        elif weeks < 12:
            return f"Approximately {int(weeks)} weeks ({int(weeks/4)} months) with consistent practice"
        else:
            months = int(weeks / 4)
            return f"Approximately {months} months with consistent practice and dedication"
