"""Centralized error handling for the application."""

from typing import Optional, Callable, Any
from functools import wraps
import traceback

from utils.logger import get_logger

logger = get_logger(__name__)


class RecommenderException(Exception):
    """Base exception for all recommender system errors."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """
        Initialize exception.
        
        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class CVParsingError(RecommenderException):
    """Error during CV parsing."""
    pass


class JobAnalysisError(RecommenderException):
    """Error during job description analysis."""
    pass


class SkillGapAnalysisError(RecommenderException):
    """Error during skill gap analysis."""
    pass


class ProjectRecommendationError(RecommenderException):
    """Error during project recommendation generation."""
    pass


class APIError(RecommenderException):
    """Error during external API calls."""
    
    def __init__(
        self,
        message: str,
        api_name: str,
        status_code: Optional[int] = None,
        details: Optional[dict] = None
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            api_name: Name of the API (GitHub, YouTube, etc.)
            status_code: HTTP status code
            details: Additional error details
        """
        details = details or {}
        details["api_name"] = api_name
        if status_code:
            details["status_code"] = status_code
        
        super().__init__(message, details)
        self.api_name = api_name
        self.status_code = status_code


class RateLimitError(APIError):
    """Error when API rate limit is exceeded."""
    
    def __init__(self, api_name: str, retry_after: Optional[int] = None):
        """
        Initialize rate limit error.
        
        Args:
            api_name: Name of the API
            retry_after: Seconds to wait before retrying
        """
        message = f"Rate limit exceeded for {api_name}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, api_name, status_code=429, details=details)
        self.retry_after = retry_after


class ConfigurationError(RecommenderException):
    """Error in application configuration."""
    pass


def handle_errors(
    default_return: Any = None,
    raise_on_error: bool = False,
    log_traceback: bool = True
):
    """
    Decorator for handling errors in functions.
    
    Args:
        default_return: Value to return on error
        raise_on_error: Whether to re-raise the exception
        log_traceback: Whether to log full traceback
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RecommenderException as e:
                logger.error(f"Error in {func.__name__}: {e.message}", extra={"details": e.details})
                if log_traceback:
                    logger.debug(traceback.format_exc())
                
                if raise_on_error:
                    raise
                return default_return
            
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
                if log_traceback:
                    logger.debug(traceback.format_exc())
                
                if raise_on_error:
                    raise RecommenderException(
                        f"Unexpected error in {func.__name__}",
                        details={"original_error": str(e)}
                    )
                return default_return
        
        return wrapper
    return decorator


def format_error_for_user(error: Exception) -> str:
    """
    Format error message for user display.
    
    Args:
        error: Exception to format
    
    Returns:
        User-friendly error message
    """
    if isinstance(error, CVParsingError):
        return f"❌ Failed to parse CV: {error.message}. Please ensure the file is a valid PDF or DOCX."
    
    elif isinstance(error, JobAnalysisError):
        return f"❌ Failed to analyze job description: {error.message}. Please check the job description text."
    
    elif isinstance(error, RateLimitError):
        msg = f"⏱️ API rate limit exceeded for {error.api_name}."
        if error.retry_after:
            msg += f" Please wait {error.retry_after} seconds."
        return msg
    
    elif isinstance(error, APIError):
        return f"🌐 API error ({error.api_name}): {error.message}. Please try again later."
    
    elif isinstance(error, ConfigurationError):
        return f"⚙️ Configuration error: {error.message}. Please check your settings."
    
    elif isinstance(error, RecommenderException):
        return f"❌ Error: {error.message}"
    
    else:
        return f"❌ An unexpected error occurred: {str(error)}. Please try again."


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions on error.
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier for delay
        exceptions: Tuple of exceptions to catch
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries failed for {func.__name__}")
            
            # All retries exhausted
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator
