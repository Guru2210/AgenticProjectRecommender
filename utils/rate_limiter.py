"""Rate limiting for API calls."""

import time
from threading import Lock
from collections import deque
from typing import Dict, Optional
from datetime import datetime, timedelta

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class TokenBucket:
    """Token bucket algorithm for rate limiting."""
    
    def __init__(self, rate: int, per: int = 60):
        """
        Initialize token bucket.
        
        Args:
            rate: Number of tokens (requests) allowed
            per: Time period in seconds (default: 60 seconds)
        """
        self.rate = rate
        self.per = per
        self.tokens = rate
        self.last_update = time.time()
        self.lock = Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        
        Args:
            tokens: Number of tokens to consume
        
        Returns:
            True if tokens were consumed, False if rate limit exceeded
        """
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Refill tokens based on elapsed time
            self.tokens = min(
                self.rate,
                self.tokens + (elapsed * self.rate / self.per)
            )
            self.last_update = now
            
            # Try to consume tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def wait_time(self) -> float:
        """
        Get time to wait until next token is available.
        
        Returns:
            Wait time in seconds
        """
        with self.lock:
            if self.tokens >= 1:
                return 0.0
            
            tokens_needed = 1 - self.tokens
            return (tokens_needed * self.per) / self.rate


class SlidingWindowRateLimiter:
    """Sliding window rate limiter."""
    
    def __init__(self, rate: int, window: int = 60):
        """
        Initialize sliding window rate limiter.
        
        Args:
            rate: Number of requests allowed
            window: Time window in seconds
        """
        self.rate = rate
        self.window = window
        self.requests = deque()
        self.lock = Lock()
    
    def is_allowed(self) -> bool:
        """
        Check if request is allowed.
        
        Returns:
            True if allowed, False if rate limit exceeded
        """
        with self.lock:
            now = time.time()
            cutoff = now - self.window
            
            # Remove old requests outside the window
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()
            
            # Check if we can add a new request
            if len(self.requests) < self.rate:
                self.requests.append(now)
                return True
            
            return False
    
    def wait_time(self) -> float:
        """
        Get time to wait until next request is allowed.
        
        Returns:
            Wait time in seconds
        """
        with self.lock:
            if len(self.requests) < self.rate:
                return 0.0
            
            # Time until oldest request expires
            oldest = self.requests[0]
            now = time.time()
            return max(0.0, (oldest + self.window) - now)


class RateLimiter:
    """
    Unified rate limiter for different APIs.
    Manages separate rate limits for GitHub, YouTube, and LLM APIs.
    """
    
    def __init__(self):
        """Initialize rate limiters for different services."""
        self.limiters: Dict[str, TokenBucket] = {}
        
        if settings.enable_rate_limiting:
            self.limiters["github"] = TokenBucket(
                rate=settings.github_rate_limit,
                per=60  # per minute
            )
            self.limiters["youtube"] = TokenBucket(
                rate=settings.youtube_rate_limit,
                per=60  # per minute
            )
            self.limiters["llm"] = TokenBucket(
                rate=settings.llm_rate_limit,
                per=60  # per minute
            )
            logger.info("Rate limiting enabled")
        else:
            logger.info("Rate limiting disabled")
    
    def acquire(self, service: str, tokens: int = 1, wait: bool = True) -> bool:
        """
        Acquire tokens for a service.
        
        Args:
            service: Service name (github, youtube, llm)
            tokens: Number of tokens to acquire
            wait: Whether to wait if rate limit is exceeded
        
        Returns:
            True if tokens acquired, False if rate limit exceeded and wait=False
        """
        if not settings.enable_rate_limiting:
            return True
        
        if service not in self.limiters:
            logger.warning(f"Unknown service: {service}")
            return True
        
        limiter = self.limiters[service]
        
        # Try to consume tokens
        if limiter.consume(tokens):
            logger.debug(f"Rate limit OK for {service}")
            return True
        
        # Rate limit exceeded
        if wait:
            wait_time = limiter.wait_time()
            logger.warning(f"Rate limit exceeded for {service}. Waiting {wait_time:.2f}s")
            time.sleep(wait_time)
            return limiter.consume(tokens)
        else:
            logger.warning(f"Rate limit exceeded for {service}")
            return False
    
    def get_wait_time(self, service: str) -> float:
        """
        Get wait time for a service.
        
        Args:
            service: Service name
        
        Returns:
            Wait time in seconds
        """
        if not settings.enable_rate_limiting or service not in self.limiters:
            return 0.0
        
        return self.limiters[service].wait_time()
    
    def reset(self, service: Optional[str] = None) -> None:
        """
        Reset rate limiter for a service or all services.
        
        Args:
            service: Service name (None = reset all)
        """
        if service:
            if service in self.limiters:
                self.limiters[service] = TokenBucket(
                    rate=getattr(settings, f"{service}_rate_limit"),
                    per=60
                )
                logger.info(f"Rate limiter reset for {service}")
        else:
            self.__init__()
            logger.info("All rate limiters reset")


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limited(service: str, tokens: int = 1, wait: bool = True):
    """
    Decorator for rate-limited functions.
    
    Args:
        service: Service name (github, youtube, llm)
        tokens: Number of tokens to consume
        wait: Whether to wait if rate limit exceeded
    
    Returns:
        Decorated function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if rate_limiter.acquire(service, tokens, wait):
                return func(*args, **kwargs)
            else:
                raise Exception(f"Rate limit exceeded for {service}")
        return wrapper
    return decorator
