"""GitHub API integration for searching repositories."""

import requests
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from config import settings
from models.recommendation_models import Resource, ResourceType
from utils.logger import get_logger
from utils.cache import cached
from utils.rate_limiter import rate_limiter
from utils.error_handler import APIError, RateLimitError, retry_on_error

logger = get_logger(__name__)


class GitHubSearchClient:
    """Client for searching GitHub repositories."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self):
        """Initialize GitHub search client."""
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        if settings.github_token:
            self.headers["Authorization"] = f"token {settings.github_token}"
            logger.info("GitHub client initialized with authentication")
        else:
            logger.warning("GitHub client initialized without authentication (rate limits apply)")
    
    @retry_on_error(max_retries=3, delay=2.0, exceptions=(APIError,))
    @cached(ttl=3600, key_prefix="github")
    def search_repositories(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: int = 10,
        max_results: int = 5,
        sort: str = "stars"
    ) -> List[Resource]:
        """
        Search GitHub repositories.
        
        Args:
            query: Search query (skill/technology name)
            language: Programming language filter
            min_stars: Minimum number of stars
            max_results: Maximum number of results
            sort: Sort by (stars, forks, updated)
        
        Returns:
            List of Resource objects
        """
        logger.info(f"Searching GitHub for: {query}")
        
        # Acquire rate limit token
        rate_limiter.acquire("github", wait=True)
        
        # Build search query
        search_query = query
        if language:
            search_query += f" language:{language}"
        search_query += f" stars:>={min_stars}"
        
        params = {
            "q": search_query,
            "sort": sort,
            "order": "desc",
            "per_page": max_results
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/search/repositories",
                headers=self.headers,
                params=params,
                timeout=10
            )
            
            # Check for rate limiting
            if response.status_code == 403:
                reset_time = response.headers.get("X-RateLimit-Reset")
                if reset_time:
                    retry_after = int(reset_time) - int(datetime.now().timestamp())
                    raise RateLimitError("github", retry_after=max(0, retry_after))
            
            response.raise_for_status()
            
            data = response.json()
            repositories = data.get("items", [])
            
            logger.info(f"Found {len(repositories)} repositories for '{query}'")
            
            # Convert to Resource objects
            resources = []
            for repo in repositories:
                resource = Resource(
                    type=ResourceType.GITHUB,
                    title=repo["name"],
                    url=repo["html_url"],
                    description=repo.get("description", ""),
                    stars=repo.get("stargazers_count", 0),
                    language=repo.get("language"),
                    last_updated=repo.get("updated_at"),
                    relevance_score=self._calculate_relevance(repo, query)
                )
                resources.append(resource)
            
            # Sort by relevance score
            resources.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
            return resources
        
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API request failed: {str(e)}")
            raise APIError(
                f"Failed to search GitHub: {str(e)}",
                api_name="GitHub",
                status_code=getattr(e.response, "status_code", None) if hasattr(e, "response") else None
            )
    
    def search_by_skill(
        self,
        skill: str,
        project_type: Optional[str] = None,
        max_results: int = 5
    ) -> List[Resource]:
        """
        Search repositories for a specific skill.
        
        Args:
            skill: Skill name (e.g., "React", "Python")
            project_type: Optional project type (e.g., "tutorial", "example")
            max_results: Maximum number of results
        
        Returns:
            List of Resource objects
        """
        query = skill
        if project_type:
            query += f" {project_type}"
        
        return self.search_repositories(
            query=query,
            max_results=max_results
        )
    
    def search_project_examples(
        self,
        skill: str,
        difficulty: str = "beginner",
        max_results: int = 3
    ) -> List[Resource]:
        """
        Search for project examples for a skill.
        
        Args:
            skill: Skill name
            difficulty: Difficulty level (beginner, intermediate, advanced)
            max_results: Maximum number of results
        
        Returns:
            List of Resource objects
        """
        query = f"{skill} {difficulty} project example"
        
        return self.search_repositories(
            query=query,
            max_results=max_results,
            min_stars=5
        )
    
    def _calculate_relevance(self, repo: Dict[str, Any], query: str) -> float:
        """
        Calculate relevance score for a repository.
        
        Args:
            repo: Repository data from GitHub API
            query: Search query
        
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        
        # Name match
        name = repo.get("name", "").lower()
        if query.lower() in name:
            score += 0.3
        
        # Description match
        description = repo.get("description", "").lower()
        if description and query.lower() in description:
            score += 0.2
        
        # Stars (normalized)
        stars = repo.get("stargazers_count", 0)
        if stars > 0:
            # Logarithmic scale for stars
            import math
            score += min(0.3, math.log10(stars + 1) / 10)
        
        # Recent activity
        updated_at = repo.get("updated_at")
        if updated_at:
            try:
                updated_date = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                days_since_update = (datetime.now(updated_date.tzinfo) - updated_date).days
                
                # Bonus for recent updates (within 6 months)
                if days_since_update < 180:
                    score += 0.2 * (1 - days_since_update / 180)
            except:
                pass
        
        return min(1.0, score)
    
    def get_repository_details(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get detailed information about a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
        
        Returns:
            Repository details
        """
        rate_limiter.acquire("github", wait=True)
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get repository details: {str(e)}")
            raise APIError(
                f"Failed to get repository details: {str(e)}",
                api_name="GitHub"
            )
