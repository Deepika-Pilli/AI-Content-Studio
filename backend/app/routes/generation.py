"""
AI content generation route.

Provides endpoints for generating content using the Groq LLM
with support for different content types, tones, and parameters.
"""

import logging

from fastapi import APIRouter, HTTPException
from app.models.request_models import GenerateRequest
from app.models.response_models import GenerateResponse, ErrorResponse
from app.services.groq_service import GroqService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/generate", tags=["generation"])

# Service instance (singleton pattern)
groq_service = GroqService()


@router.post(
    "/",
    response_model=GenerateResponse,
    summary="Generate AI content",
    description=(
        "Generates content using the Groq LLM based on a prompt, "
        "content type, tone, and other parameters. Supports LinkedIn posts, "
        "blog articles, tweets, emails, and general content."
    ),
    responses={
        200: {"model": GenerateResponse, "description": "Content generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        503: {"model": ErrorResponse, "description": "LLM service unavailable"},
    },
)
async def generate_content(request: GenerateRequest) -> GenerateResponse:
    """
    Generate content using the Groq LLM.

    Accepts a prompt with optional configuration for content type,
    tone, token limit, and temperature.

    Args:
        request: The generation request containing prompt and parameters.

    Returns:
        GenerateResponse with the generated content and metadata.

    Raises:
        HTTPException 400: If the prompt is empty or invalid.
        HTTPException 503: If the LLM service is unavailable or fails.
    """
    if not groq_service.is_available:
        logger.error("Groq LLM is not available. API key may be missing.")
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "LLM service is not available",
                "detail": (
                    "Groq API key is not configured. "
                    "Please set GROQ_API_KEY in your .env file and restart the server."
                ),
            },
        )

    try:
        logger.info(
            "Processing generation request: content_type=%s, tone=%s",
            request.content_type,
            request.tone,
        )

        result = groq_service.generate_sync(
            prompt=request.prompt,
            content_type=request.content_type or "general",
            tone=request.tone or "professional",
            max_tokens=request.max_tokens or 512,
            temperature=request.temperature or 0.7,
        )

        return GenerateResponse(
            success=True,
            content=result["content"],
            model=result["model"],
            content_type=result["content_type"],
            usage=result.get("usage"),
        )

    except RuntimeError as exc:
        logger.exception("Generation failed for prompt: %.50s...", request.prompt)
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Content generation failed",
                "detail": str(exc),
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error during content generation")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc),
            },
        )


@router.get(
    "/",
    summary="Simple GET generation (deprecated)",
    description=(
        "Legacy endpoint. Generates a short default LinkedIn post "
        "about Artificial Intelligence. Prefer the POST endpoint for "
        "full control over generation parameters."
    ),
    response_model=GenerateResponse,
)
async def generate_get() -> GenerateResponse:
    """
    Simple GET generation endpoint for quick testing.

    This preserves backward compatibility with the original /generate GET endpoint.
    For production use, prefer the POST endpoint with full parameter control.

    Returns:
        GenerateResponse with a default AI-generated LinkedIn post.
    """
    if not groq_service.is_available:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "LLM service is not available",
                "detail": "Groq API key is not configured.",
            },
        )

    try:
        result = groq_service.generate_sync(
            prompt="Write a short LinkedIn post about Artificial Intelligence.",
            content_type="linkedin",
            tone="professional",
            max_tokens=300,
            temperature=0.7,
        )

        return GenerateResponse(
            success=True,
            content=result["content"],
            model=result["model"],
            content_type=result["content_type"],
            usage=result.get("usage"),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": "Content generation failed",
                "detail": str(exc),
            },
        )