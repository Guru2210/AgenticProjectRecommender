"""
Configuration management for the CV Project Recommender system.
Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model to use")
    openai_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    
    # GitHub API
    github_token: Optional[str] = Field(default=None, description="GitHub personal access token")
    
    # YouTube Data API
    youtube_api_key: str = Field(..., description="YouTube Data API key")
    
    # Google Custom Search API
    google_api_key: Optional[str] = Field(default=None, description="Google Custom Search API key")
    google_search_engine_id: Optional[str] = Field(default=None, description="Google Custom Search Engine ID")
    
    # Application Settings
    app_name: str = Field(default="CV Project Recommender", description="Application name")
    log_level: str = Field(default="INFO", description="Logging level")
    cache_enabled: bool = Field(default=True, description="Enable caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Rate Limiting
    github_rate_limit: int = Field(default=30, description="GitHub API calls per minute")
    youtube_rate_limit: int = Field(default=10, description="YouTube API calls per minute")
    google_rate_limit: int = Field(default=100, description="Google API calls per day")
    llm_rate_limit: int = Field(default=50, description="LLM API calls per minute")
    
    # Redis Cache (optional)
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    
    # Feature Flags
    enable_caching: bool = Field(default=True, description="Enable caching feature")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    
    # Backend Configuration
    backend_url: str = Field(default="http://localhost:8000", description="Backend API URL")
    job_retention_seconds: int = Field(default=3600, description="How long to keep completed jobs (seconds)")

    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# Global settings instance
settings = Settings()
