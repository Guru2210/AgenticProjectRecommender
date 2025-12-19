"""Guardrails module for input validation, output validation, and safety checks."""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import magic  # python-magic for file type detection

from utils.logger import get_logger

logger = get_logger(__name__)


class GuardrailViolationType(Enum):
    """Types of guardrail violations."""
    FILE_TOO_LARGE = "file_too_large"
    INVALID_FILE_TYPE = "invalid_file_type"
    INVALID_CONTENT = "invalid_content"
    PROMPT_INJECTION = "prompt_injection"
    PII_DETECTED = "pii_detected"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_OUTPUT = "invalid_output"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    violation_type: Optional[GuardrailViolationType] = None
    message: str = ""
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class PIIMatch:
    """Detected PII in text."""
    type: str  # email, phone, ssn, etc.
    value: str
    start: int
    end: int


class InputValidator:
    """Validates user inputs against security and quality standards."""
    
    # File validation constants
    MAX_FILE_SIZE_MB = 10
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_MIME_TYPES = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # DOCX
        'application/msword',  # DOC
        'text/plain',
    ]
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt']
    
    # Text validation constants
    MIN_JOB_DESCRIPTION_LENGTH = 50
    MAX_JOB_DESCRIPTION_LENGTH = 10000
    
    @staticmethod
    def validate_file_upload(file_path: str, file_size: int, filename: str) -> ValidationResult:
        """
        Validate uploaded file.
        
        Args:
            file_path: Path to uploaded file
            file_size: Size of file in bytes
            filename: Original filename
        
        Returns:
            ValidationResult
        """
        # Check file size
        if file_size > InputValidator.MAX_FILE_SIZE_BYTES:
            return ValidationResult(
                is_valid=False,
                violation_type=GuardrailViolationType.FILE_TOO_LARGE,
                message=f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum allowed size ({InputValidator.MAX_FILE_SIZE_MB}MB)",
                details={"file_size": file_size, "max_size": InputValidator.MAX_FILE_SIZE_BYTES}
            )
        
        # Check file extension
        file_ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if file_ext not in InputValidator.ALLOWED_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                violation_type=GuardrailViolationType.INVALID_FILE_TYPE,
                message=f"File type '{file_ext}' not allowed. Allowed types: {', '.join(InputValidator.ALLOWED_EXTENSIONS)}",
                details={"extension": file_ext, "allowed": InputValidator.ALLOWED_EXTENSIONS}
            )
        
        # Verify actual file type using magic numbers
        try:
            mime = magic.Magic(mime=True)
            detected_type = mime.from_file(file_path)
            
            if detected_type not in InputValidator.ALLOWED_MIME_TYPES:
                return ValidationResult(
                    is_valid=False,
                    violation_type=GuardrailViolationType.INVALID_FILE_TYPE,
                    message=f"File content type '{detected_type}' doesn't match extension or is not allowed",
                    details={"detected_type": detected_type, "extension": file_ext}
                )
        except Exception as e:
            logger.warning(f"Could not verify file type: {str(e)}")
            # Continue if magic fails - better to allow than block legitimate files
        
        return ValidationResult(is_valid=True, message="File validation passed")
    
    @staticmethod
    def validate_job_description(text: str) -> ValidationResult:
        """
        Validate job description text.
        
        Args:
            text: Job description text
        
        Returns:
            ValidationResult
        """
        if not text or not text.strip():
            return ValidationResult(
                is_valid=False,
                violation_type=GuardrailViolationType.INVALID_CONTENT,
                message="Job description cannot be empty"
            )
        
        text_length = len(text.strip())
        
        if text_length < InputValidator.MIN_JOB_DESCRIPTION_LENGTH:
            return ValidationResult(
                is_valid=False,
                violation_type=GuardrailViolationType.INVALID_CONTENT,
                message=f"Job description too short ({text_length} chars). Minimum: {InputValidator.MIN_JOB_DESCRIPTION_LENGTH} chars",
                details={"length": text_length, "min_length": InputValidator.MIN_JOB_DESCRIPTION_LENGTH}
            )
        
        if text_length > InputValidator.MAX_JOB_DESCRIPTION_LENGTH:
            return ValidationResult(
                is_valid=False,
                violation_type=GuardrailViolationType.INVALID_CONTENT,
                message=f"Job description too long ({text_length} chars). Maximum: {InputValidator.MAX_JOB_DESCRIPTION_LENGTH} chars",
                details={"length": text_length, "max_length": InputValidator.MAX_JOB_DESCRIPTION_LENGTH}
            )
        
        return ValidationResult(is_valid=True, message="Job description validation passed")


class PromptInjectionDetector:
    """Detects potential prompt injection attacks."""
    
    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|above|all)\s+instructions?",
        r"disregard\s+(previous|above|all)",
        r"forget\s+(previous|above|all)",
        r"you\s+are\s+now",
        r"new\s+instructions?",
        r"system\s+prompt",
        r"<\|im_start\|>",  # Special tokens
        r"<\|im_end\|>",
        r"<\|endoftext\|>",
        r"###\s*instruction",
        r"act\s+as\s+(?:a\s+)?(?:different|new)",
        r"pretend\s+(?:to\s+be|you\s+are)",
    ]
    
    @staticmethod
    def detect(text: str) -> ValidationResult:
        """
        Detect potential prompt injection in text.
        
        Args:
            text: Text to check
        
        Returns:
            ValidationResult
        """
        text_lower = text.lower()
        
        for pattern in PromptInjectionDetector.INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Potential prompt injection detected: pattern '{pattern}'")
                return ValidationResult(
                    is_valid=False,
                    violation_type=GuardrailViolationType.PROMPT_INJECTION,
                    message="Potential prompt injection detected in input",
                    details={"pattern": pattern}
                )
        
        return ValidationResult(is_valid=True, message="No prompt injection detected")


class PIIDetector:
    """Detects and masks Personally Identifiable Information (PII)."""
    
    # Regex patterns for common PII
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PHONE_PATTERN = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
    SSN_PATTERN = r'\b\d{3}-\d{2}-\d{4}\b'
    
    @staticmethod
    def detect_pii(text: str) -> List[PIIMatch]:
        """
        Detect PII in text.
        
        Args:
            text: Text to scan for PII
        
        Returns:
            List of PIIMatch objects
        """
        matches = []
        
        # Detect emails
        for match in re.finditer(PIIDetector.EMAIL_PATTERN, text):
            matches.append(PIIMatch(
                type="email",
                value=match.group(),
                start=match.start(),
                end=match.end()
            ))
        
        # Detect phone numbers
        for match in re.finditer(PIIDetector.PHONE_PATTERN, text):
            matches.append(PIIMatch(
                type="phone",
                value=match.group(),
                start=match.start(),
                end=match.end()
            ))
        
        # Detect SSN
        for match in re.finditer(PIIDetector.SSN_PATTERN, text):
            matches.append(PIIMatch(
                type="ssn",
                value=match.group(),
                start=match.start(),
                end=match.end()
            ))
        
        return matches
    
    @staticmethod
    def mask_pii(text: str) -> Tuple[str, List[PIIMatch]]:
        """
        Mask PII in text.
        
        Args:
            text: Text to mask
        
        Returns:
            Tuple of (masked_text, list of detected PII)
        """
        pii_matches = PIIDetector.detect_pii(text)
        
        if not pii_matches:
            return text, []
        
        # Sort matches by position (reverse order to maintain indices)
        pii_matches.sort(key=lambda x: x.start, reverse=True)
        
        masked_text = text
        for match in pii_matches:
            mask = f"[{match.type.upper()}]"
            masked_text = masked_text[:match.start] + mask + masked_text[match.end:]
        
        logger.info(f"Masked {len(pii_matches)} PII instances")
        
        return masked_text, pii_matches


class ContentModerator:
    """Moderates content for inappropriate or offensive material."""
    
    # Basic profanity/inappropriate content patterns
    # In production, use a more comprehensive list or external API
    INAPPROPRIATE_PATTERNS = [
        r'\b(?:fuck|shit|damn|bitch|asshole|bastard)\b',
        # Add more patterns as needed
    ]
    
    @staticmethod
    def check_content(text: str) -> ValidationResult:
        """
        Check content for inappropriate material.
        
        Args:
            text: Text to check
        
        Returns:
            ValidationResult
        """
        text_lower = text.lower()
        
        for pattern in ContentModerator.INAPPROPRIATE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning("Inappropriate content detected")
                return ValidationResult(
                    is_valid=False,
                    violation_type=GuardrailViolationType.INAPPROPRIATE_CONTENT,
                    message="Inappropriate content detected in input",
                    details={"pattern": pattern}
                )
        
        return ValidationResult(is_valid=True, message="Content moderation passed")


class OutputValidator:
    """Validates AI-generated outputs for quality and safety."""
    
    @staticmethod
    def validate_recommendation_result(result: Dict[str, Any]) -> ValidationResult:
        """
        Validate recommendation result structure and content.
        
        Args:
            result: Recommendation result dictionary
        
        Returns:
            ValidationResult
        """
        # Check required fields
        required_fields = ['skill_match_analysis', 'skill_gap_recommendations', 'overall_assessment']
        
        for field in required_fields:
            if field not in result:
                return ValidationResult(
                    is_valid=False,
                    violation_type=GuardrailViolationType.INVALID_OUTPUT,
                    message=f"Missing required field: {field}",
                    details={"missing_field": field}
                )
        
        # Validate skill match analysis
        skill_match = result.get('skill_match_analysis', {})
        match_percentage = skill_match.get('match_percentage')
        
        if match_percentage is not None:
            if not isinstance(match_percentage, (int, float)) or not (0 <= match_percentage <= 100):
                return ValidationResult(
                    is_valid=False,
                    violation_type=GuardrailViolationType.INVALID_OUTPUT,
                    message=f"Invalid match percentage: {match_percentage}",
                    details={"match_percentage": match_percentage}
                )
        
        # Check for reasonable number of recommendations
        recommendations = result.get('skill_gap_recommendations', [])
        if len(recommendations) > 20:
            logger.warning(f"Unusually high number of recommendations: {len(recommendations)}")
        
        return ValidationResult(is_valid=True, message="Output validation passed")


# Singleton instances
input_validator = InputValidator()
prompt_injection_detector = PromptInjectionDetector()
pii_detector = PIIDetector()
content_moderator = ContentModerator()
output_validator = OutputValidator()
