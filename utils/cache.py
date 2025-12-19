"""Caching mechanism for API responses and expensive operations."""

import json
import hashlib
from typing import Optional, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
import pickle

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class InMemoryCache:
    """Simple in-memory cache implementation."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize in-memory cache.
        
        Args:
            ttl: Time to live in seconds
        """
        self._cache = {}
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                logger.debug(f"Cache hit: {key}")
                return value
            else:
                # Expired
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        ttl = ttl or self._ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def size(self) -> int:
        """Get number of items in cache."""
        # Clean expired entries first
        now = datetime.now()
        expired_keys = [k for k, (_, expiry) in self._cache.items() if now >= expiry]
        for key in expired_keys:
            del self._cache[key]
        
        return len(self._cache)


class RedisCache:
    """Redis-based cache implementation."""
    
    def __init__(self, ttl: int = 3600):
        """
        Initialize Redis cache.
        
        Args:
            ttl: Time to live in seconds
        """
        try:
            import redis
            self._redis = redis.from_url(settings.redis_url, decode_responses=False)
            self._ttl = ttl
            self._redis.ping()  # Test connection
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}. Falling back to in-memory cache.")
            self._redis = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self._redis:
            return None
        
        try:
            value = self._redis.get(key)
            if value:
                logger.debug(f"Redis cache hit: {key}")
                return pickle.loads(value)
            logger.debug(f"Redis cache miss: {key}")
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis cache."""
        if not self._redis:
            return
        
        try:
            ttl = ttl or self._ttl
            serialized = pickle.dumps(value)
            self._redis.setex(key, ttl, serialized)
            logger.debug(f"Redis cache set: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    def delete(self, key: str) -> None:
        """Delete value from Redis cache."""
        if not self._redis:
            return
        
        try:
            self._redis.delete(key)
            logger.debug(f"Redis cache deleted: {key}")
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
    
    def clear(self) -> None:
        """Clear all cache entries."""
        if not self._redis:
            return
        
        try:
            self._redis.flushdb()
            logger.info("Redis cache cleared")
        except Exception as e:
            logger.error(f"Redis clear error: {e}")


class CacheManager:
    """Unified cache manager that can use different backends."""
    
    def __init__(self):
        """Initialize cache manager with appropriate backend."""
        if settings.enable_caching:
            # Try Redis first, fall back to in-memory
            try:
                self._cache = RedisCache(ttl=settings.cache_ttl)
                if self._cache._redis is None:
                    raise Exception("Redis not available")
                self._backend = "redis"
            except:
                self._cache = InMemoryCache(ttl=settings.cache_ttl)
                self._backend = "memory"
            
            logger.info(f"Cache initialized with {self._backend} backend")
        else:
            self._cache = None
            self._backend = "disabled"
            logger.info("Caching disabled")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self._cache:
            return None
        return self._cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        if self._cache:
            self._cache.set(key, value, ttl)
    
    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if self._cache:
            self._cache.delete(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        if self._cache:
            self._cache.clear()
    
    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """
        Generate a cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Cache key string
        """
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()


# Global cache manager instance
cache_manager = CacheManager()


def cached(ttl: Optional[int] = None, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds (None = use default)
        key_prefix: Prefix for cache key
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not settings.enable_caching:
                return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{cache_manager.generate_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
