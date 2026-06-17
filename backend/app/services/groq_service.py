"""
Groq LLM service layer.

Handles all interactions with the Groq API through LangChain,
including content generation with dynamic prompt construction.
"""

import logging
from typing import Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings

logger = logging.getLogger(__name__)


class GroqService:
    """
    Service class for interacting with Groq LLM models.

    Provides methods for generating content with configurable
    parameters like prompt, content type, tone, and temperature.
    """

    def __init__(self) -> None:
        """Initialize the Groq LLM client using settings from config."""
        self._llm: Optional[ChatGroq] = None
        self._initialize_llm()

    def _initialize_llm(self) -> None:
        """Create the ChatGroq instance if an API key is available."""
        if settings.is_groq_configured:
            self._llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_MODEL,
            )
            logger.info(
                "Groq LLM initialized with model: %s",
                settings.GROQ_MODEL,
            )
        else:
            logger.warning("Groq API key not found. LLM will not be available.")

    @property
    def is_available(self) -> bool:
        """Check if the Groq LLM client is initialized and ready."""
        return self._llm is not None

    def _build_system_prompt(
        self,
        content_type: str = "general",
        tone: str = "professional",
    ) -> str:
        """
        Build a system prompt based on content type and tone.

        Args:
            content_type: The type of content (linkedin, blog, twitter, email, general).
            tone: Desired tone (professional, casual, humorous, formal).

        Returns:
            A formatted system prompt string.
        """
        tone_descriptions = {
            "professional": (
                "Use a professional, polished, and authoritative tone. "
                "Avoid slang and overly casual language."
            ),
            "casual": (
                "Use a casual, friendly, and conversational tone. "
                "Write as if speaking to a colleague."
            ),
            "humorous": (
                "Use a witty, humorous, and engaging tone. "
                "Include light-hearted elements and clever wordplay."
            ),
            "formal": (
                "Use a formal, academic, and structured tone. "
                "Maintain a high level of professionalism and precision."
            ),
        }

        type_instructions = {
            "linkedin": (
                "Write a LinkedIn post. Include a strong hook, "
                "valuable insights, and relevant hashtags. "
                "Keep it between 150-300 words."
            ),
            "blog": (
                "Write a blog article. Include an introduction, "
                "well-structured body paragraphs, and a conclusion. "
                "Use subheadings and bullet points where appropriate. "
                "Aim for 300-800 words."
            ),
            "twitter": (
                "Write a Twitter/X post. Be concise and impactful. "
                "Maximum 280 characters. Include relevant hashtags."
            ),
            "email": (
                "Write an email. Include a subject line, greeting, "
                "body content, and professional closing signature."
            ),
            "general": (
                "Write a general piece of content. "
                "Ensure clarity, coherence, and reader engagement."
            ),
        }

        tone_instruction = tone_descriptions.get(
            tone, tone_descriptions["professional"]
        )
        type_instruction = type_instructions.get(
            content_type, type_instructions["general"]
        )

        return (
            f"You are an expert content creator. "
            f"Tone: {tone_instruction} "
            f"Format: {type_instruction} "
            "Generate high-quality, original content based on the user's prompt."
        )

    async def generate(
        self,
        prompt: str,
        content_type: str = "general",
        tone: str = "professional",
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> dict:
        """
        Generate content using the Groq LLM.

        Args:
            prompt: The user's input prompt for content generation.
            content_type: Type of content (linkedin, blog, twitter, email, general).
            tone: Desired tone (professional, casual, humorous, formal).
            max_tokens: Maximum tokens for the generated response.
            temperature: Sampling temperature (0.0 - 2.0).

        Returns:
            A dictionary with generated content and metadata.

        Raises:
            RuntimeError: If the LLM is not initialized (API key missing).
        """
        if not self.is_available:
            raise RuntimeError(
                "Groq LLM is not available. Please check your API key configuration."
            )

        system_prompt = self._build_system_prompt(
            content_type=content_type,
            tone=tone,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]

        try:
            logger.debug(
                "Generating content with prompt (truncated): %.100s...",
                prompt,
            )

            response = await self._llm.ainvoke(
                messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            result = {
                "content": response.content,
                "model": settings.GROQ_MODEL,
                "content_type": content_type,
                "usage": (
                    {
                        "prompt_tokens": (
                            response.response_metadata.get("token_usage", {}).get(
                                "prompt_tokens", 0
                            )
                        ),
                        "completion_tokens": (
                            response.response_metadata.get("token_usage", {}).get(
                                "completion_tokens", 0
                            )
                        ),
                        "total_tokens": (
                            response.response_metadata.get("token_usage", {}).get(
                                "total_tokens", 0
                            )
                        ),
                    }
                    if hasattr(response, "response_metadata")
                    else None
                ),
            }

            logger.info(
                "Content generated successfully with model: %s",
                settings.GROQ_MODEL,
            )
            return result

        except Exception as exc:
            logger.exception("Groq API call failed: %s", exc)
            raise RuntimeError(
                f"Content generation failed: {str(exc)}"
            ) from exc

    def generate_sync(
        self,
        prompt: str,
        content_type: str = "general",
        tone: str = "professional",
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> dict:
        """
        Synchronous wrapper for content generation.

        Args:
            prompt: The user's input prompt for content generation.
            content_type: Type of content (linkedin, blog, twitter, email, general).
            tone: Desired tone (professional, casual, humorous, formal).
            max_tokens: Maximum tokens for the generated response.
            temperature: Sampling temperature (0.0 - 2.0).

        Returns:
            A dictionary with generated content and metadata.
        """
        if not self.is_available:
            raise RuntimeError(
                "Groq LLM is not available. Please check your API key configuration."
            )

        system_prompt = self._build_system_prompt(
            content_type=content_type,
            tone=tone,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=prompt),
        ]

        try:
            logger.debug(
                "Generating content (sync) with prompt (truncated): %.100s...",
                prompt,
            )

            response = self._llm.invoke(
                messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            result = {
                "content": response.content,
                "model": settings.GROQ_MODEL,
                "content_type": content_type,
                "usage": (
                    {
                        "prompt_tokens": (
                            response.response_metadata.get("token_usage", {}).get(
                                "prompt_tokens", 0
                            )
                        ),
                        "completion_tokens": (
                            response.response_metadata.get("token_usage", {}).get(
                                "completion_tokens", 0
                            )
                        ),
                        "total_tokens": (
                            response.response_metadata.get("token_usage", {}).get(
                                "total_tokens", 0
                            )
                        ),
                    }
                    if hasattr(response, "response_metadata")
                    else None
                ),
            }

            logger.info(
                "Content generated successfully (sync) with model: %s",
                settings.GROQ_MODEL,
            )
            return result

        except Exception as exc:
            logger.exception("Groq API call failed (sync): %s", exc)
            raise RuntimeError(
                f"Content generation failed: {str(exc)}"
            ) from exc