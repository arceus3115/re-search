"""
AI client for LLM interactions using Google Gemini Flash API.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv

    # Load .env from backend directory (parent of app directory)
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv not installed, continue without it

logger = logging.getLogger(__name__)

# Gemini API key - hardcoded (can be overridden via GEMINI_API_KEY environment variable)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
_gemini_model = None
try:
    import google.generativeai as genai

    genai.configure(api_key=GEMINI_API_KEY)
    _gemini_model = genai.GenerativeModel("gemini-2.0-flash")

    # Validate API key by making a test call (non-blocking - server will start even if validation fails)
    try:
        test_config = genai.types.GenerationConfig(max_output_tokens=1)
        test_response = _gemini_model.generate_content(
            "test", generation_config=test_config
        )
        logger.info("Gemini Flash API initialized and validated successfully")
    except Exception as validation_error:
        error_msg = str(validation_error)
        if (
            "API key" in error_msg
            or "API_KEY" in error_msg
            or "expired" in error_msg.lower()
            or "INVALID" in error_msg
        ):
            logger.warning(f"Gemini API key validation failed: {error_msg}")
            logger.warning(
                "Server will start, but AI features may not work. Please check your API key."
            )
            logger.warning("Get a new key from: https://aistudio.google.com/app/apikey")
            # Don't raise - allow server to start, API calls will fail later with better context
        else:
            # If validation fails for other reasons, log warning but continue
            logger.warning(
                f"API key validation test failed (non-critical): {error_msg}"
            )
            logger.info("Gemini Flash API initialized (validation skipped)")

except ImportError:
    logger.error(
        "google-generativeai package not installed. Run: pip install google-generativeai"
    )
    raise RuntimeError(
        "google-generativeai package not installed. "
        "Run: pip install google-generativeai"
    )
except Exception as e:
    error_msg = str(e)
    logger.error(f"Failed to initialize Gemini API: {error_msg}")
    # Don't prevent server from starting - log error and continue
    logger.warning("Server will start, but AI features may not work.")
    _gemini_model = None


class AIClient:
    """
    Client for interacting with Google Gemini Flash API.
    """

    def __init__(self):
        """Initialize AI client with Gemini Flash."""
        self.model = _gemini_model
        if not self.model:
            raise RuntimeError("Gemini API not initialized. Check API key.")

    def generate_text(
        self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7
    ) -> str:
        """
        Generate text using Gemini Flash.

        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens to generate (Gemini uses max_output_tokens)
            temperature: Temperature for generation (0.0-1.0)

        Returns:
            Generated text string

        Raises:
            ValueError: If API key is invalid or expired
            RuntimeError: For other API errors
        """
        try:
            import google.generativeai as genai

            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            response = self.model.generate_content(
                prompt, generation_config=generation_config
            )

            if response and response.text:
                return response.text.strip()
            else:
                logger.warning("Empty response from Gemini API")
                return ""

        except Exception as e:
            error_msg = str(e)

            # Check for API key errors
            if (
                "API key" in error_msg
                or "API_KEY" in error_msg
                or "expired" in error_msg.lower()
            ):
                logger.error(f"Gemini API key error: {error_msg}")
                raise ValueError(
                    "Gemini API key is invalid or expired. "
                    "Please set a valid API key in the GEMINI_API_KEY environment variable. "
                    "Get a new key from: https://aistudio.google.com/app/apikey"
                ) from e
            else:
                logger.error(
                    f"Error generating text with Gemini: {error_msg}", exc_info=True
                )
                raise RuntimeError(f"Gemini API error: {error_msg}") from e

    def generate_structured(
        self,
        prompt: str,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate structured response (for JSON-like outputs).

        Args:
            prompt: The prompt to send
            response_format: Optional format specification
            temperature: Temperature for generation

        Returns:
            Dictionary with generated content
        """
        # Add instruction to format as JSON if response_format provided
        if response_format:
            prompt = f"{prompt}\n\nFormat your response as JSON with the following structure: {response_format}"

        text = self.generate_text(prompt, temperature=temperature)

        # Try to parse as JSON if response_format was provided
        if response_format:
            try:
                import json

                return json.loads(text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse response as JSON, returning as text")
                return {"content": text}

        return {"content": text}


# Singleton instance
_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """Get or create singleton AI client instance."""
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client
