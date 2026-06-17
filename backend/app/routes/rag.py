"""
RAG (Retrieval-Augmented Generation) query route.

Provides an endpoint for asking questions about an indexed document.
Retrieves relevant chunks, builds a grounded prompt, and generates
an answer using the Groq LLM.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.rag.rag_service import rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------

from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
    """Request body for a RAG query."""

    document_id: str = Field(
        ...,
        min_length=1,
        description="ID of the indexed document to query",
        example="upload_a01c7f06_test_rag_doc.txt",
    )
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The question to answer based on the document",
        example="What does AI do in healthcare?",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of context chunks to retrieve (1-10)",
        example=3,
    )


class RetrievedChunk(BaseModel):
    """A single chunk retrieved as context for the answer."""

    chunk_index: int = Field(..., description="Index of the chunk in the document")
    text: str = Field(..., description="The chunk text content")
    source: str = Field(..., description="Source document filename")
    document_id: str = Field(..., description="Document identifier")
    score: float = Field(
        ...,
        description="Cosine similarity score (0-1, higher = more relevant)",
    )
    chunk_size: int = Field(..., description="Number of characters in the chunk")


class RagQueryResponse(BaseModel):
    """Response from a successful RAG query."""

    success: bool = Field(default=True, description="Whether the query succeeded")
    answer: str = Field(..., description="The generated answer text")
    question: str = Field(..., description="The original question")
    document_id: str = Field(..., description="The document that was queried")
    retrieved_chunks: List[RetrievedChunk] = Field(
        ...,
        description="Chunks retrieved and used as context",
    )
    total_chunks_retrieved: int = Field(
        ...,
        description="Number of chunks retrieved",
    )
    model: str = Field(
        ...,
        description="LLM model used for answer generation",
    )


class RagErrorResponse(BaseModel):
    """Error response for failed RAG queries."""

    success: bool = Field(default=False, description="Always False for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error info")


# ------------------------------------------------------------------
# Endpoint
# ------------------------------------------------------------------


@router.post(
    "/query",
    response_model=RagQueryResponse,
    summary="Ask a question about a document",
    description=(
        "Ask a natural language question about an indexed document. "
        "The system will:\n"
        "1. Retrieve the most relevant chunks from the document's FAISS index\n"
        "2. Build a grounded context from those chunks\n"
        "3. Generate an answer using the Groq LLM based solely on the context\n"
        "4. Return the answer along with source chunks and relevance scores\n\n"
        "**Prerequisites:**\n"
        "1. Upload the document via POST /upload/\n"
        "2. Index it via POST /index/{document_id}"
    ),
    responses={
        200: {"model": RagQueryResponse, "description": "Answer generated successfully"},
        404: {"model": RagErrorResponse, "description": "Document index not found"},
        503: {"model": RagErrorResponse, "description": "LLM service unavailable"},
        500: {"model": RagErrorResponse, "description": "RAG pipeline failed"},
    },
)
async def rag_query(request: RagQueryRequest) -> RagQueryResponse:
    """
    Execute a RAG query against an indexed document.

    Args:
        request: The RAG query request (document_id, question, top_k).

    Returns:
        RagQueryResponse with the generated answer and source chunks.

    Raises:
        HTTPException 404: If the document has not been indexed.
        HTTPException 503: If the LLM service is unavailable.
        HTTPException 500: If the pipeline fails unexpectedly.
    """
    logger.info(
        "RAG query request: document_id=%s, question=%.60s..., top_k=%d",
        request.document_id,
        request.question,
        request.top_k,
    )

    try:
        result = rag_service.query(
            document_id=request.document_id,
            question=request.question,
            top_k=request.top_k,
        )

        logger.info(
            "RAG query successful: answer=%d chars, %d chunks, model=%s",
            len(result.get("answer", "")),
            result.get("total_chunks_retrieved", 0),
            result.get("model", "unknown"),
        )

        return RagQueryResponse(
            success=True,
            answer=result["answer"],
            question=result["question"],
            document_id=result["document_id"],
            retrieved_chunks=[RetrievedChunk(**c) for c in result["retrieved_chunks"]],
            total_chunks_retrieved=result["total_chunks_retrieved"],
            model=result["model"],
        )

    except FileNotFoundError as exc:
        logger.warning("RAG query failed - index not found: %s", exc)
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
        logger.exception("RAG pipeline failed")
        # Distinguish between LLM failures and other runtime errors
        if "Answer generation failed" in str(exc) or "Groq" in str(exc):
            raise HTTPException(
                status_code=503,
                detail={
                    "success": False,
                    "error": "LLM service error",
                    "detail": str(exc),
                },
            )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "RAG pipeline failed",
                "detail": str(exc),
            },
        )
    except Exception as exc:
        logger.exception("Unexpected RAG query error")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc),
            },
        )