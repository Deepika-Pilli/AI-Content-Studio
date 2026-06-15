"""
API route modules for the AI Content Studio.

Routes are organized by domain:
- health: Service health check and configuration status
- generation: AI content generation endpoints
- upload: Document upload and processing
"""

from .health import router as health_router
from .generation import router as generation_router
from .upload import router as upload_router
from .indexing import router as indexing_router
from .retrieval import router as retrieval_router
from .rag import router as rag_router

__all__ = [
    "health_router",
    "generation_router",
    "upload_router",
    "indexing_router",
    "retrieval_router",
    "rag_router",
]
