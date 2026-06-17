"""
Document retrieval route.

Provides an endpoint for searching an indexed document's chunks
using semantic similarity. Queries are embedded with HuggingFace
and matched against the FAISS index.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.rag.retrieval_service import retrieval_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/retrieve", tags=["retrieval"])


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    """Request body for document retrieval."""

    document_id: str = Field(
        ...,
        min_length=1,
        description="ID of the indexed document to search",
        example="upload_a01c7f06_test_rag_doc.txt",
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Search query to find relevant chunks",
        example="What does AI do in healthcare?",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of top results to return (1-50)",
        example=5,
    )


class ChunkResult(BaseModel):
    """A single retrieved chunk from the document."""

    chunk_index: int = Field(..., description="Index of the chunk in the document")
    text: str = Field(..., description="The chunk text content")
    source: str = Field(..., description="Source document filename")
    document_id: str = Field(..., description="Document identifier")
    score: float = Field(..., description="Cosine similarity score (0-1, higher = better)")
    chunk_size: int = Field(..., description="Number of characters in the chunk")


class RetrieveResponse(BaseModel):
    """Response from a successful retrieval query."""

    success: bool = Field(default=True, description="Whether retrieval succeeded")
    document_id: str = Field(..., description="The document that was searched")
    query: str = Field(..., description="The original search query")
    total_results: int = Field(..., description="Number of results returned")
    results: List[ChunkResult] = Field(..., description="Top matching chunks")


class RetrieveErrorResponse(BaseModel):
    """Error response for failed retrieval."""

    success: bool = Field(default=False, description="Always False for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error info")


# ------------------------------------------------------------------
# Endpoint
# ------------------------------------------------------------------


@router.post(
    "/",
    response_model=RetrieveResponse,
    summary="Search document chunks",
    description=(
        "Search an indexed document using semantic similarity. "
        "The query is embedded using HuggingFace sentence-transformers "
        "and matched against the document's FAISS index.\n\n"
        "**Step 1:** Upload a document via POST /upload/\n"
        "**Step 2:** Index it via POST /index/{document_id}\n"
        "**Step 3:** Search it via this endpoint"
    ),
    responses={
        200: {"model": RetrieveResponse, "description": "Retrieval successful"},
        404: {"model": RetrieveErrorResponse, "description": "Document index not found"},
        422: {"model": RetrieveErrorResponse, "description": "Validation error"},
        500: {"model": RetrieveErrorResponse, "description": "Retrieval pipeline failed"},
    },
)
async def retrieve(
    request: RetrieveRequest,
) -> RetrieveResponse:
    """
    Retrieve the most relevant chunks from an indexed document.

    Args:
        request: The retrieval request (document_id, query, top_k).

    Returns:
        RetrieveResponse with ranked list of matching chunks.

    Raises:
        HTTPException 404: If the document has not been indexed.
        HTTPException 500: If the retrieval pipeline fails.
    """
    logger.info(
        "Retrieval request: document_id=%s, query=%.50s..., top_k=%d",
        request.document_id,
        request.query,
        request.top_k,
    )

    try:
        results = retrieval_service.retrieve(
            document_id=request.document_id,
            query=request.query,
            top_k=request.top_k,
        )

        chunk_results = [
            ChunkResult(**r.to_dict()) for r in results
        ]

        logger.info(
            "Retrieval successful: %d results from '%s'",
            len(chunk_results),
            request.document_id,
        )

        return RetrieveResponse(
            success=True,
            document_id=request.document_id,
            query=request.query,
            total_results=len(chunk_results),
            results=chunk_results,
        )

    except FileNotFoundError as exc:
        logger.warning("Index not found: %s", exc)
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "Document index not found",
                "detail": str(exc),
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "success": False,
                "error": "Invalid request",
                "detail": str(exc),
            },
        )
    except RuntimeError as exc:
        logger.exception("Retrieval pipeline failed")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Retrieval pipeline failed",
                "detail": str(exc),
            },
        )
    except Exception as exc:
        logger.exception("Unexpected retrieval error")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc),
            },
        )


# Keep a simple GET endpoint for quick testing
@router.get(
    "/{document_id}",
    response_model=RetrieveResponse,
    summary="Quick retrieval test (GET)",
    description="Simple GET-based retrieval for testing. Prefer POST for production.",
)
async def retrieve_get(
    document_id: str,
    query: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(default=5, ge=1, le=50, description="Number of results"),
) -> RetrieveResponse:
    """
    Quick retrieval via GET parameters for testing.

    Args:
        document_id: ID of the indexed document.
        query: The search query.
        top_k: Number of results (1-50).

    Returns:
        RetrieveResponse with matching chunks.
    """
    logger.info("GET retrieval: doc=%s, query=%.50s...", document_id, query)

    try:
        results = retrieval_service.retrieve(
            document_id=document_id,
            query=query,
            top_k=top_k,
        )

        return RetrieveResponse(
            success=True,
            document_id=document_id,
            query=query,
            total_results=len(results),
            results=[ChunkResult(**r.to_dict()) for r in results],
        )

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"success": False, "error": str(exc)})
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(exc)},
        )