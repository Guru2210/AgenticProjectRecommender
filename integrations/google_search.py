"""Google Custom Search API integration for finding project links and tutorials."""

import requests
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import settings
from models.recommendation_models import Resource, ResourceType
from utils.logger import get_logger
from utils.cache import cached
from utils.rate_limiter import rate_limiter
from utils.error_handler import APIError, RateLimitError, retry_on_error

logger = get_logger(__name__)


class GoogleSearchClient:
    """Client for searching the web using Google Custom Search API."""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    # Trusted domains for quality filtering
    TRUSTED_DOMAINS = [
        "dev.to",
        "medium.com",
        "freecodecamp.org",
        "realpython.com",
        "digitalocean.com",
        "hackernoon.com",
        "towardsdatascience.com",
        "css-tricks.com",
        "smashingmagazine.com",
        "scotch.io",
        "tutorialspoint.com",
        "geeksforgeeks.org",
        "stackoverflow.com",
        "github.io",
        "readthedocs.io",
        "docs.python.org",
        "developer.mozilla.org",
    ]
    
    def __init__(self):
        """Initialize Google search client."""
        self.api_key = settings.google_api_key
        self.search_engine_id = settings.google_search_engine_id
        
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Custom Search API not configured (missing API key or search engine ID)")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Google Custom Search client initialized")
    
    @retry_on_error(max_retries=2, delay=1.0, exceptions=(APIError,))
    @cached(ttl=86400, key_prefix="google_search")  # Cache for 24 hours
    def search(
        self,
        query: str,
        max_results: int = 5,
        date_restrict: str = "y2"  # Last 2 years
    ) -> List[Resource]:
        """
        Search the web using Google Custom Search API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            date_restrict: Date restriction (e.g., 'y2' for last 2 years)
        
        Returns:
            List of Resource objects
        """
        if not self.enabled:
            logger.warning("Google search is disabled (API not configured)")
            return []
        
        logger.info(f"Searching Google for: {query}")
        
        # Acquire rate limit token
        rate_limiter.acquire("google", wait=True)
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(max_results, 10),  # API max is 10
            "dateRestrict": date_restrict,
        }
        
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=10
            )
            
            # Check for quota exceeded
            if response.status_code == 429:
                raise RateLimitError("google", retry_after=3600)
            
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            logger.info(f"Found {len(items)} results for '{query}'")
            
            # Convert to Resource objects
            resources = []
            for item in items:
                # Filter by trusted domains
                url = item.get("link", "")
                if not self._is_trusted_domain(url):
                    logger.debug(f"Skipping untrusted domain: {url}")
                    continue
                
                resource = Resource(
                    type=ResourceType.TUTORIAL,
                    title=item.get("title", ""),
                    url=url,
                    description=item.get("snippet", ""),
                    relevance_score=self._calculate_relevance(item, query)
                )
                resources.append(resource)
            
            # Sort by relevance score
            resources.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
            return resources[:max_results]
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Google API request failed: {str(e)}")
            # Don't raise error, just return empty list for graceful degradation
            return []
    
    def search_project_tutorials(
        self,
        skill: str,
        difficulty: str = "beginner",
        max_results: int = 3
    ) -> List[Resource]:
        """
        Search for project tutorials for a specific skill.
        
        Args:
            skill: Skill name (e.g., "React", "Python")
            difficulty: Difficulty level
            max_results: Maximum number of results
        
        Returns:
            List of Resource objects
        """
        query = f"{skill} {difficulty} project tutorial"
        return self.search(query=query, max_results=max_results)
    
    def search_learning_resources(
        self,
        skill: str,
        max_results: int = 3
    ) -> List[Resource]:
        """
        Search for general learning resources for a skill.
        
        Args:
            skill: Skill name
            max_results: Maximum number of results
        
        Returns:
            List of Resource objects
        """
        queries = [
            f"{skill} tutorial for beginners",
            f"learn {skill} step by step",
            f"{skill} getting started guide",
        ]
        
        all_resources = []
        results_per_query = max(1, max_results // len(queries))
        
        for query in queries:
            resources = self.search(query=query, max_results=results_per_query)
            all_resources.extend(resources)
        
        # Deduplicate by URL
        seen_urls = set()
        unique_resources = []
        for resource in all_resources:
            if resource.url not in seen_urls:
                seen_urls.add(resource.url)
                unique_resources.append(resource)
        
        # Sort by relevance and return top results
        unique_resources.sort(key=lambda x: x.relevance_score or 0, reverse=True)
        return unique_resources[:max_results]
    
    def _is_trusted_domain(self, url: str) -> bool:
        """
        Check if URL is from a trusted domain.
        
        Args:
            url: URL to check
        
        Returns:
            True if trusted, False otherwise
        """
        url_lower = url.lower()
        return any(domain in url_lower for domain in self.TRUSTED_DOMAINS)
    
    def _calculate_relevance(self, item: Dict[str, Any], query: str) -> float:
        """
        Calculate relevance score for a search result.
        
        Args:
            item: Search result item from Google API
            query: Search query
        
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        query_lower = query.lower()
        
        # Title match
        title = item.get("title", "").lower()
        if query_lower in title:
            score += 0.4
        
        # Snippet match
        snippet = item.get("snippet", "").lower()
        if query_lower in snippet:
            score += 0.3
        
        # Domain quality bonus
        url = item.get("link", "").lower()
        high_quality_domains = ["freecodecamp.org", "realpython.com", "developer.mozilla.org"]
        if any(domain in url for domain in high_quality_domains):
            score += 0.3
        
        return min(1.0, score)


# Create singleton instance
google_search_client = GoogleSearchClient()
