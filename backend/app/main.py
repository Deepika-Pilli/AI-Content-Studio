"""
AI Content Studio - Backend API

A FastAPI application for AI-powered content generation using Groq LLM.
Provides endpoints for generating LinkedIn posts, blogs, tweets, emails,
and general content with configurable tone and parameters.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware import AuthMiddleware
from app.routes import (
    health_router,
    generation_router,
    upload_router,
    indexing_router,
    retrieval_router,
    rag_router,
)

# ---------------------------------------------------------------------------
# Logging Configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-5s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=(
        "AI-powered content generation API. "
        "Supports multiple content types (LinkedIn, Blog, Twitter, Email) "
        "with configurable tone, length, and creativity."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS Middleware (allow React dev server on localhost:5173)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Auth Middleware (requires X-API-Key header on protected routes)
# ---------------------------------------------------------------------------
app.add_middleware(AuthMiddleware)

# ---------------------------------------------------------------------------
# Route Registration
# ---------------------------------------------------------------------------

# Health check routes (root "/" and "/test-key")
app.include_router(health_router, prefix="", tags=["health"])

# AI generation routes (POST/GET "/generate")
app.include_router(generation_router, prefix="", tags=["generation"])

# Document upload routes (POST "/upload")
app.include_router(upload_router, prefix="", tags=["upload"])

# Document indexing routes (POST "/index/{document_id}")
app.include_router(indexing_router, prefix="", tags=["indexing"])

# Document retrieval routes (POST/GET "/retrieve")
app.include_router(retrieval_router, prefix="", tags=["retrieval"])

# RAG query routes (POST "/rag/query")
app.include_router(rag_router, prefix="", tags=["rag"])

# ---------------------------------------------------------------------------
# Startup Event
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def startup_event() -> None:
    """Log application startup and configuration status."""
    logger.info("=" * 60)
    logger.info("  %s v%s", settings.APP_TITLE, settings.APP_VERSION)
    logger.info("=" * 60)
    logger.info("  Groq API configured : %s", settings.is_groq_configured)
    logger.info("  Model              : %s", settings.GROQ_MODEL)
    logger.info("  Chunk size         : %d", settings.CHUNK_SIZE)
    logger.info("  Chunk overlap      : %d", settings.CHUNK_OVERLAP)
    logger.info("  Embedding model    : %s", settings.EMBEDDING_MODEL)
    logger.info("  Embedding dim      : %d", settings.EMBEDDING_DIMENSION)
    logger.info("  Docs (Swagger)     : /docs")
    logger.info("  Docs (ReDoc)       : /redoc")
    logger.info("=" * 60)
