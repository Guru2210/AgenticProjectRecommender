"""LLM client wrapper for LangChain integration."""

from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from config import settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter
from utils.error_handler import APIError, retry_on_error

logger = get_logger(__name__)


class LLMClient:
    """Wrapper for LLM interactions using LangChain."""
    
    def __init__(self):
        """Initialize LLM client."""
        try:
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                openai_api_key=settings.openai_api_key,
                max_retries=2
            )
            logger.info(f"LLM client initialized with model: {settings.openai_model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {str(e)}")
            raise APIError(
                f"Failed to initialize LLM: {str(e)}",
                api_name="OpenAI"
            )
    
    @retry_on_error(max_retries=3, delay=2.0, backoff=2.0, exceptions=(APIError,))
    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            temperature: Optional temperature override
        
        Returns:
            Generated text
        """
        # Acquire rate limit token
        rate_limiter.acquire("llm", wait=True)
        
        messages = []
        
        if system_message:
            messages.append(SystemMessage(content=system_message))
        
        messages.append(HumanMessage(content=prompt))
        
        try:
            # Override temperature if specified
            if temperature is not None:
                llm = ChatOpenAI(
                    model=settings.openai_model,
                    temperature=temperature,
                    openai_api_key=settings.openai_api_key
                )
            else:
                llm = self.llm
            
            response = llm.invoke(messages)
            
            logger.debug(f"LLM generation successful (prompt length: {len(prompt)})")
            
            return response.content
        
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise APIError(
                f"LLM generation failed: {str(e)}",
                api_name="OpenAI"
            )
    
    def generate_structured(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        response_format: str = "json"
    ) -> str:
        """
        Generate structured output (JSON).
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            response_format: Expected format (json, yaml, etc.)
        
        Returns:
            Generated structured text
        """
        # Add format instruction to prompt
        format_instruction = f"\n\nPlease respond in valid {response_format.upper()} format only."
        full_prompt = prompt + format_instruction
        
        return self.generate(full_prompt, system_message)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None
    ) -> str:
        """
        Multi-turn chat conversation.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Optional temperature override
        
        Returns:
            Generated response
        """
        rate_limiter.acquire("llm", wait=True)
        
        # Convert to LangChain message format
        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))
        
        try:
            if temperature is not None:
                llm = ChatOpenAI(
                    model=settings.openai_model,
                    temperature=temperature,
                    openai_api_key=settings.openai_api_key
                )
            else:
                llm = self.llm
            
            response = llm.invoke(lc_messages)
            return response.content
        
        except Exception as e:
            logger.error(f"LLM chat failed: {str(e)}")
            raise APIError(
                f"LLM chat failed: {str(e)}",
                api_name="OpenAI"
            )
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Estimated token count
        """
        try:
            import tiktoken
            
            # Get encoding for the model
            if "gpt-4" in settings.openai_model:
                encoding = tiktoken.encoding_for_model("gpt-4")
            else:
                encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            
            tokens = encoding.encode(text)
            return len(tokens)
        
        except Exception as e:
            logger.warning(f"Token counting failed: {str(e)}. Using rough estimate.")
            # Rough estimate: 1 token ≈ 4 characters
            return len(text) // 4
    
    def validate_api_key(self) -> bool:
        """
        Validate that the API key works.
        
        Returns:
            True if valid, False otherwise
        """
        try:
            self.generate("Test", temperature=0.0)
            logger.info("API key validation successful")
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False


# Global LLM client instance
llm_client = LLMClient()
