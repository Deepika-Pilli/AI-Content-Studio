"""
Document indexing route.

Provides endpoints for triggering the full indexing pipeline
(chunking → embeddings → FAISS) on an already-uploaded document,
and listing all indexed documents.
"""

import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.config import settings
from app.rag.indexing_service import indexing_service
from app.rag.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/index", tags=["indexing"])


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------


class IndexResponse(BaseModel):
    """Response returned after successfully indexing a document."""

    success: bool = Field(default=True, description="Whether indexing succeeded")
    message: str = Field(..., description="Human-readable result message")
    document_id: str = Field(..., description="The document identifier used")
    total_chunks: int = Field(..., description="Number of text chunks created")
    total_vectors: int = Field(..., description="Number of vectors stored in FAISS")
    embedding_dimension: int = Field(..., description="Dimension of embedding vectors")
    embedding_model: str = Field(..., description="Model used for embeddings")
    saved_to: str = Field(..., description="Directory where FAISS index was saved")
    index_files: list[str] = Field(..., description="Paths to saved index files")


class IndexErrorResponse(BaseModel):
    """Error response for failed indexing."""

    success: bool = Field(default=False, description="Always False for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error info")


class IndexListItem(BaseModel):
    """Summary information for an indexed document."""
    document_id: str = Field(..., description="Document identifier")
    total_chunks: int = Field(..., description="Number of chunks")
    total_vectors: int = Field(..., description="Number of vectors")


class IndexListResponse(BaseModel):
    """List of indexed documents."""
    success: bool = Field(default=True)
    total: int = Field(..., description="Total number of indexed documents")
    indexes: List[IndexListItem] = Field(..., description="List of indexed documents")


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.get(
    "/",
    response_model=IndexListResponse,
    summary="List indexed documents",
    description="Returns a list of all indexed documents with chunk and vector counts.",
)
async def list_indexes() -> IndexListResponse:
    """List all documents that have been indexed."""
    vss = VectorStoreService()
    indexes = vss.list_indexes()
    return IndexListResponse(
        success=True,
        total=len(indexes),
        indexes=[IndexListItem(**i) for i in indexes],
    )


@router.post(
    "/{document_id}",
    response_model=IndexResponse,
    summary="Index an uploaded document",
    description=(
        "Triggers the full indexing pipeline on a previously uploaded document: "
        "1. Load the extracted text from the uploaded file\n"
        "2. Split text into chunks using RecursiveCharacterTextSplitter\n"
        "3. Generate embeddings using HuggingFace sentence-transformers\n"
        "4. Store vectors in a FAISS index\n"
        "5. Persist the index and metadata to the vectors directory\n\n"
        "The document must have been previously uploaded via POST /upload/."
    ),
    responses={
        200: {"model": IndexResponse, "description": "Document indexed successfully"},
        404: {"model": IndexErrorResponse, "description": "Document file not found"},
        500: {"model": IndexErrorResponse, "description": "Indexing pipeline failed"},
    },
)
async def index_document(
    document_id: str,
    source: str = Query(
        default="",
        description="Optional source filename override for metadata",
    ),
) -> IndexResponse:
    """
    Index a previously uploaded document.

    Args:
        document_id: The document identifier (filename as returned
                     by POST /upload/ in the 'id' field).
        source: Optional source name for metadata (defaults to document_id).

    Returns:
        IndexResponse with chunk count, vector count, and file paths.

    Raises:
        HTTPException 404: If the document file is not found.
        HTTPException 500: If the indexing pipeline fails.
    """
    logger.info("Index request for document: %s", document_id)

    # Determine where the uploaded file might be
    file_path = settings.upload_path / document_id

    if not file_path.exists():
        logger.warning("Document not found: %s", file_path)
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": "Document not found",
                "detail": (
                    f"No uploaded file found with ID '{document_id}'. "
                    f"Ensure the file was uploaded via POST /upload/ "
                    f"and use the returned document 'id' field."
                ),
            },
        )

    # Read the file text
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to read document",
                "detail": f"Could not read file '{file_path}': {exc}",
            },
        )

    # Run the indexing pipeline
    try:
        result = indexing_service.index_document(
            document_id=document_id,
            text=text,
            source=source or document_id,
        )

        logger.info(
            "Indexing successful: %s (%d chunks, %d vectors)",
            document_id,
            result["total_chunks"],
            result["total_vectors"],
        )

        return IndexResponse(
            success=True,
            message=(
                f"Document '{document_id}' indexed successfully: "
                f"{result['total_chunks']} chunks → "
                f"{result['total_vectors']} vectors "
                f"(dim={result['embedding_dimension']})"
            ),
            document_id=result["document_id"],
            total_chunks=result["total_chunks"],
            total_vectors=result["total_vectors"],
            embedding_dimension=result["embedding_dimension"],
            embedding_model=result["embedding_model"],
            saved_to=result["saved_to"],
            index_files=result["index_files"],
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid document",
                "detail": str(exc),
            },
        )
    except RuntimeError as exc:
        logger.exception("Indexing pipeline failed for %s", document_id)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Indexing pipeline failed",
                "detail": str(exc),
            },
        )
    except Exception as exc:
        logger.exception("Unexpected error indexing %s", document_id)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc),
            },
        )