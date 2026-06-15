"""
Pydantic response schemas for the AI Content Studio API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class GenerateResponse(BaseModel):
    """
    Response body for successful AI content generation.

    Attributes:
        success: Whether the generation was successful.
        content: The generated text content.
        model: The model used for generation.
        content_type: The type of content generated.
        usage: Optional metadata about the generation (tokens used, etc.).
    """

    success: bool = Field(
        default=True,
        description="Whether the generation was successful",
    )
    content: str = Field(
        ...,
        description="The generated text content",
        example="Artificial intelligence is transforming healthcare by...",
    )
    model: str = Field(
        ...,
        description="The model used for generation",
        example="llama-3.3-70b-versatile",
    )
    content_type: str = Field(
        default="general",
        description="The type of content generated",
        example="linkedin",
    )
    usage: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional metadata about token usage",
    )


class HealthResponse(BaseModel):
    """
    Response body for health check endpoint.

    Attributes:
        status: Service status ("ok" or "error").
        message: Human-readable status message.
        groq_configured: Whether the Groq API key is configured.
    """

    status: str = Field(
        ...,
        description="Service status",
        example="ok",
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        example="AI Content Studio Backend Running",
    )
    groq_configured: bool = Field(
        ...,
        description="Whether the Groq API key is configured",
    )


class ErrorResponse(BaseModel):
    """
    Standard error response for API failures.

    Attributes:
        success: Always False for errors.
        error: Error message describing what went wrong.
        detail: Optional detailed error information.
    """

    success: bool = Field(
        default=False,
        description="Always false for errors",
    )
    error: str = Field(
        ...,
        description="Error message",
        example="Failed to generate content",
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information for debugging",
    )