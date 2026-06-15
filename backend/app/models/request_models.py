"""
Pydantic request schemas for the AI Content Studio API.
"""

from pydantic import BaseModel, Field
from typing import Optional


class GenerateRequest(BaseModel):
    """
    Request body for AI content generation.

    Attributes:
        prompt: The user's input prompt for content generation.
        content_type: Type of content (e.g., "linkedin", "blog", "twitter", "email").
        tone: Desired tone of the output (e.g., "professional", "casual", "humorous").
        max_tokens: Maximum tokens for the generated response.
        temperature: Sampling temperature (0.0 - 2.0) for controlling randomness.
    """

    prompt: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The user's input prompt for content generation",
        example="Write a post about the benefits of AI in healthcare",
    )
    content_type: Optional[str] = Field(
        default="general",
        description="Type of content (linkedin, blog, twitter, email, general)",
        example="linkedin",
    )
    tone: Optional[str] = Field(
        default="professional",
        description="Desired tone (professional, casual, humorous, formal)",
        example="professional",
    )
    max_tokens: Optional[int] = Field(
        default=512,
        ge=16,
        le=4096,
        description="Maximum tokens for the generated response",
        example=512,
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 - 2.0)",
        example=0.7,
    )