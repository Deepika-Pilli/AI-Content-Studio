"""
Health check route for the AI Content Studio API.

Provides endpoints to verify the service is running
and check configuration status (e.g., Groq API key).
"""

from fastapi import APIRouter
from backend.app.config import settings
from backend.app.models.response_models import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Root health check",
    description="Returns a simple status message confirming the backend is running.",
)
async def home() -> HealthResponse:
    """
    Root endpoint to verify the API is operational.

    Returns:
        HealthResponse with status "ok" and a welcome message.
    """
    return HealthResponse(
        status="ok",
        message="AI Content Studio Backend Running",
        groq_configured=settings.is_groq_configured,
    )


@router.get(
    "/healthz",
    summary="Lightweight health check for orchestrators",
    description="Returns a minimal status response. No dependencies required.",
)
async def healthz() -> dict:
    """Minimal health check for Kubernetes/Docker Compose."""
    return {"status": "ok"}


@router.get(
    "/test-key",
    response_model=HealthResponse,
    summary="Check API key configuration",
    description="Checks whether the Groq API key is configured and available.",
)
async def test_key() -> HealthResponse:
    """
    Endpoint to verify Groq API key configuration.

    Returns:
        HealthResponse indicating whether the API key is found.
    """
    if settings.is_groq_configured:
        return HealthResponse(
            status="ok",
            message="API Key Found",
            groq_configured=True,
        )
    else:
        return HealthResponse(
            status="error",
            message="API Key Missing. Set GROQ_API_KEY in your .env file.",
            groq_configured=False,
        )