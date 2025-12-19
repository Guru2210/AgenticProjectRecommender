"""CV Parser Agent - Extracts structured data from CV documents."""

import json
import re
from typing import Optional
from pathlib import Path
import PyPDF2
import docx

from models.cv_models import CVData, Skill, Experience, Education, Certification
from integrations.llm_client import llm_client
from utils.logger import get_logger
from utils.error_handler import CVParsingError, handle_errors

logger = get_logger(__name__)


class CVParserAgent:
    """Agent responsible for parsing CV documents and extracting structured data."""
    
    def __init__(self):
        """Initialize CV parser agent."""
        self.llm = llm_client
        logger.info("CV Parser Agent initialized")
    
    @handle_errors(raise_on_error=True)
    def parse_cv(self, file_path: str) -> CVData:
        """
        Parse a CV file and extract structured data.
        
        Args:
            file_path: Path to CV file (PDF or DOCX)
        
        Returns:
            CVData object with structured information
        
        Raises:
            CVParsingError: If parsing fails
        """
        logger.info(f"Parsing CV from: {file_path}")
        
        # Extract text from file
        cv_text = self._extract_text(file_path)
        
        if not cv_text or len(cv_text.strip()) < 50:
            raise CVParsingError(
                "CV file appears to be empty or too short",
                details={"file_path": file_path, "text_length": len(cv_text)}
            )
        
        # Use LLM to extract structured data
        cv_data = self._extract_structured_data(cv_text)
        
        logger.info(f"Successfully parsed CV with {len(cv_data.skills)} skills and {len(cv_data.experience)} experiences")
        
        return cv_data
    
    def _extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF or DOCX file.
        
        Args:
            file_path: Path to file
        
        Returns:
            Extracted text
        
        Raises:
            CVParsingError: If file format is unsupported or extraction fails
        """
        path = Path(file_path)
        
        if not path.exists():
            raise CVParsingError(f"File not found: {file_path}")
        
        extension = path.suffix.lower()
        
        try:
            if extension == ".pdf":
                return self._extract_from_pdf(file_path)
            elif extension in [".docx", ".doc"]:
                return self._extract_from_docx(file_path)
            else:
                raise CVParsingError(
                    f"Unsupported file format: {extension}",
                    details={"supported_formats": [".pdf", ".docx", ".doc"]}
                )
        except CVParsingError:
            raise
        except Exception as e:
            raise CVParsingError(
                f"Failed to extract text from file: {str(e)}",
                details={"file_path": file_path, "error": str(e)}
            )
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = []
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        
        return "\n".join(text)
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        doc = docx.Document(file_path)
        
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)
        
        return "\n".join(text)
    
    def _extract_structured_data(self, cv_text: str) -> CVData:
        """
        Use LLM to extract structured data from CV text.
        
        Args:
            cv_text: Raw CV text
        
        Returns:
            CVData object
        """
        system_message = """You are an expert CV parser. Extract structured information from the CV text.
Your response must be valid JSON matching this schema:
{
  "name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "summary": "string or null",
  "skills": [{"name": "string", "category": "string or null", "proficiency": "string or null", "years_of_experience": number or null}],
  "experience": [{"role": "string", "company": "string", "start_date": "string or null", "end_date": "string or null", "duration_months": number or null, "responsibilities": ["string"], "technologies": ["string"]}],
  "education": [{"degree": "string", "institution": "string", "graduation_year": number or null, "gpa": number or null, "relevant_coursework": ["string"]}],
  "certifications": [{"name": "string", "issuer": "string", "issue_date": "string or null", "expiry_date": "string or null"}],
  "total_years_experience": number or null
}

Extract as much information as possible. For skills, categorize them (e.g., Programming Language, Framework, Database, Cloud, DevOps, etc.).
For experience, extract technologies used from the job descriptions."""
        
        prompt = f"""Parse the following CV and extract structured information:

{cv_text}

Return ONLY valid JSON, no additional text."""
        
        try:
            response = self.llm.generate_structured(
                prompt=prompt,
                system_message=system_message,
                response_format="json"
            )
            
            # Clean response (remove markdown code blocks if present)
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
            
            # Convert to Pydantic model
            cv_data = CVData(**data)
            
            return cv_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            logger.debug(f"LLM response: {response[:500]}")
            raise CVParsingError(
                "Failed to parse CV data from LLM response",
                details={"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Failed to extract structured data: {str(e)}")
            raise CVParsingError(
                f"Failed to extract structured data: {str(e)}",
                details={"error": str(e)}
            )
    
    def parse_cv_text(self, cv_text: str) -> CVData:
        """
        Parse CV from text directly (useful for testing).
        
        Args:
            cv_text: CV text content
        
        Returns:
            CVData object
        """
        logger.info("Parsing CV from text")
        
        if not cv_text or len(cv_text.strip()) < 50:
            raise CVParsingError("CV text is too short")
        
        return self._extract_structured_data(cv_text)
