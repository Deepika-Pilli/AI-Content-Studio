"""
AI Content Studio - Backend API

A FastAPI application for AI-powered content generation using Groq LLM.
Provides endpoints for generating LinkedIn posts, blogs, tweets, emails,
and general content with configurable tone and parameters.
"""

import asyncio
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
# CORS Middleware (localhost dev + all Vercel deployments)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
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
    """Log application startup and configuration status.

    Immediately logs configuration and schedules a background task
    to warm up the embedding model. The background task runs via
    asyncio.to_thread so it does NOT block startup or the event loop.
    This ensures Uvicorn binds to $PORT before model download begins.
    """
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

    # ------------------------------------------------------------------
    # Background SentenceTransformer warmup (non-blocking)
    # ------------------------------------------------------------------
    # The SentenceTransformer model (~80 MB from HuggingFace) is
    # normally loaded lazily by EmbeddingsService on the first index
    # request.  That download can exceed Render's 50 s request timeout.
    #
    # We schedule a background asyncio task that calls the existing
    # lazy-load path in a thread.  Because asyncio.create_task()
    # returns immediately, Uvicorn can bind to $PORT before the
    # download even starts.  The background warmup reuses the exact
    # same embeddings_service singleton that indexing will use later.
    #
    # If the warmup fails or hasn't finished by the time the first
    # index request arrives, EmbeddingsService._load_model() still
    # lazy-loads as a fallback (the model singleton is thread-safe
    # because _load_model is guarded by a simple "if None" check).
    # ------------------------------------------------------------------

    async def _warmup_embeddings() -> None:
        logger.info(
            "Warming up embedding model '%s' in background thread ...",
            settings.EMBEDDING_MODEL,
        )
        try:
            from app.rag.embeddings import embeddings_service

            # Run the blocking model download in a thread pool so it
            # does not stall the asyncio event loop.
            await asyncio.to_thread(embeddings_service._get_model)

            logger.info(
                "Embedding model '%s' warm-up complete (loaded=%s)",
                settings.EMBEDDING_MODEL,
                embeddings_service.is_loaded,
            )
        except Exception as exc:
            logger.warning(
                "Embedding model warm-up failed: %s. "
                "Lazy loading will be used as fallback on first index request.",
                exc,
            )

    # Schedule the background task.  create_task returns immediately;
    # the actual model download will start after the event loop resumes.
    asyncio.create_task(_warmup_embeddings())
    logger.info("Startup complete – port binding is unblocked.")