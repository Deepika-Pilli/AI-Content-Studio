"""
API Key authentication middleware.

Validates the X-API-Key header on protected routes.
Public routes (/, /docs, /redoc, /openapi.json, /test-key) are excluded.
"""

import logging
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.app.config import settings

logger = logging.getLogger(__name__)

# Routes that do NOT require authentication
PUBLIC_PATHS = {
    "/",
    "/healthz",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/test-key",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that checks X-API-Key header on protected endpoints."""

    async def dispatch(self, request: Request, call_next):
        # Skip auth for public paths
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith(("/docs/", "/redoc/")):
            return await call_next(request)

        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            logger.warning("Missing API key: %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=401,
                content={
                    "success": False,
                    "error": "Authentication required",
                    "detail": "Provide your API key via the X-API-Key header.",
                },
            )

        if api_key != settings.API_KEY:
            logger.warning("Invalid API key: %s %s", request.method, request.url.path)
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "Invalid API key",
                    "detail": "The provided API key is invalid.",
                },
            )

        return await call_next(request)