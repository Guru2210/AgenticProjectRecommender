"""YouTube Data API integration for searching videos."""

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


class YouTubeSearchClient:
    """Client for searching YouTube videos."""
    
    BASE_URL = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self):
        """Initialize YouTube search client."""
        if not settings.youtube_api_key:
            logger.warning("YouTube API key not configured")
        else:
            logger.info("YouTube client initialized")
    
    @retry_on_error(max_retries=3, delay=2.0, exceptions=(APIError,))
    @cached(ttl=3600, key_prefix="youtube")
    def search_videos(
        self,
        query: str,
        max_results: int = 5,
        order: str = "relevance",
        video_duration: Optional[str] = None
    ) -> List[Resource]:
        """
        Search YouTube videos.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            order: Sort order (relevance, viewCount, rating, date)
            video_duration: Duration filter (short, medium, long)
        
        Returns:
            List of Resource objects
        """
        logger.info(f"Searching YouTube for: {query}")
        
        # Acquire rate limit token
        rate_limiter.acquire("youtube", wait=True)
        
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": order,
            "key": settings.youtube_api_key,
            "relevanceLanguage": "en",
            "safeSearch": "moderate"
        }
        
        if video_duration:
            params["videoDuration"] = video_duration
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=10
            )
            
            # Check for quota exceeded
            if response.status_code == 403:
                error_data = response.json()
                if "quotaExceeded" in str(error_data):
                    raise RateLimitError("YouTube", retry_after=86400)  # 24 hours
            
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            logger.info(f"Found {len(items)} videos for '{query}'")
            
            # Get video IDs to fetch additional details
            video_ids = [item["id"]["videoId"] for item in items]
            
            # Fetch video statistics and details
            video_details = self._get_video_details(video_ids) if video_ids else {}
            
            # Convert to Resource objects
            resources = []
            for item in items:
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                details = video_details.get(video_id, {})
                
                resource = Resource(
                    type=ResourceType.YOUTUBE,
                    title=snippet.get("title", ""),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    description=snippet.get("description", ""),
                    channel=snippet.get("channelTitle", ""),
                    duration=details.get("duration"),
                    views=details.get("viewCount"),
                    relevance_score=self._calculate_relevance(item, details, query)
                )
                resources.append(resource)
            
            # Sort by relevance score
            resources.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
            return resources
        
        except requests.exceptions.RequestException as e:
            logger.error(f"YouTube API request failed: {str(e)}")
            raise APIError(
                f"Failed to search YouTube: {str(e)}",
                api_name="YouTube",
                status_code=getattr(e.response, "status_code", None) if hasattr(e, "response") else None
            )
    
    def search_tutorials(
        self,
        skill: str,
        difficulty: str = "beginner",
        max_results: int = 5
    ) -> List[Resource]:
        """
        Search for tutorial videos for a specific skill.
        
        Args:
            skill: Skill name
            difficulty: Difficulty level (beginner, intermediate, advanced)
            max_results: Maximum number of results
        
        Returns:
            List of Resource objects
        """
        query = f"{skill} tutorial {difficulty}"
        
        return self.search_videos(
            query=query,
            max_results=max_results,
            order="relevance"
        )
    
    def search_project_walkthroughs(
        self,
        skill: str,
        project_type: str,
        max_results: int = 3
    ) -> List[Resource]:
        """
        Search for project walkthrough videos.
        
        Args:
            skill: Skill name
            project_type: Type of project
            max_results: Maximum number of results
        
        Returns:
            List of Resource objects
        """
        query = f"{skill} {project_type} project walkthrough"
        
        return self.search_videos(
            query=query,
            max_results=max_results,
            video_duration="medium"  # Prefer medium-length videos
        )
    
    def _get_video_details(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information for videos.
        
        Args:
            video_ids: List of video IDs
        
        Returns:
            Dictionary mapping video ID to details
        """
        if not video_ids:
            return {}
        
        rate_limiter.acquire("youtube", wait=True)
        
        params = {
            "part": "contentDetails,statistics",
            "id": ",".join(video_ids),
            "key": settings.youtube_api_key
        }
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/videos",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            details = {}
            for item in items:
                video_id = item["id"]
                content_details = item.get("contentDetails", {})
                statistics = item.get("statistics", {})
                
                details[video_id] = {
                    "duration": self._parse_duration(content_details.get("duration", "")),
                    "viewCount": int(statistics.get("viewCount", 0)),
                    "likeCount": int(statistics.get("likeCount", 0)),
                    "commentCount": int(statistics.get("commentCount", 0))
                }
            
            return details
        
        except Exception as e:
            logger.warning(f"Failed to get video details: {str(e)}")
            return {}
    
    def _parse_duration(self, duration: str) -> str:
        """
        Parse ISO 8601 duration to human-readable format.
        
        Args:
            duration: ISO 8601 duration string (e.g., "PT15M33S")
        
        Returns:
            Human-readable duration (e.g., "15:33")
        """
        import re
        
        if not duration:
            return ""
        
        # Parse PT15M33S format
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return duration
        
        hours, minutes, seconds = match.groups()
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def _calculate_relevance(
        self,
        item: Dict[str, Any],
        details: Dict[str, Any],
        query: str
    ) -> float:
        """
        Calculate relevance score for a video.
        
        Args:
            item: Video item from search results
            details: Video details (views, likes, etc.)
            query: Search query
        
        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.0
        
        snippet = item.get("snippet", {})
        
        # Title match
        title = snippet.get("title", "").lower()
        if query.lower() in title:
            score += 0.3
        
        # Description match
        description = snippet.get("description", "").lower()
        if query.lower() in description:
            score += 0.2
        
        # View count (normalized)
        views = details.get("viewCount", 0)
        if views > 0:
            import math
            # Logarithmic scale for views
            score += min(0.3, math.log10(views + 1) / 15)
        
        # Engagement (likes/views ratio)
        likes = details.get("likeCount", 0)
        if views > 0 and likes > 0:
            engagement = likes / views
            score += min(0.2, engagement * 20)
        
        return min(1.0, score)
