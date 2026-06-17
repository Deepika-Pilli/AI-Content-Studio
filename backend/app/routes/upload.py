"""
Document upload route.

Provides an endpoint for uploading PDF, DOCX, and TXT files.
Validates file type and size, saves to disk, extracts text,
and returns document metadata.
"""

import logging

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.models.upload_models import UploadResponse, UploadErrorResponse
from app.services.upload_service import upload_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


class UploadListItem(BaseModel):
    """Summary information for an uploaded document."""
    id: str = Field(..., description="Document identifier")
    file_size_bytes: int = Field(..., description="File size in bytes")
    file_size_display: str = Field(..., description="Human-readable file size")
    uploaded_at: str = Field(..., description="Upload timestamp")


class UploadListResponse(BaseModel):
    """List of uploaded documents."""
    success: bool = Field(default=True)
    total: int = Field(..., description="Total number of uploaded documents")
    documents: List[UploadListItem] = Field(..., description="List of uploaded documents")


@router.get(
    "/",
    response_model=UploadListResponse,
    summary="List uploaded documents",
    description="Returns a list of all uploaded documents with metadata.",
)
async def list_uploads() -> UploadListResponse:
    """List all documents that have been uploaded."""
    documents = upload_service.list_uploads()
    return UploadListResponse(
        success=True,
        total=len(documents),
        documents=[UploadListItem(**d) for d in documents],
    )


@router.post(
    "/",
    response_model=UploadResponse,
    summary="Upload a document",
    description=(
        "Upload a PDF, DOCX, or TXT file. The file is validated for type and size, "
        "saved to the uploads directory, and text content is extracted. "
        "Returns detailed metadata about the uploaded document.\n\n"
        "**Supported formats:** PDF, DOCX, TXT\n"
        "**Max file size:** 10 MB (configurable via MAX_FILE_SIZE_MB env var)"
    ),
    responses={
        200: {"model": UploadResponse, "description": "File uploaded successfully"},
        400: {"model": UploadErrorResponse, "description": "Invalid file or validation error"},
        413: {"model": UploadErrorResponse, "description": "File too large"},
        500: {"model": UploadErrorResponse, "description": "Internal server error"},
    },
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a document file for processing.

    Accepts a file upload, validates it, saves it to the uploads
    directory, extracts text content, and returns metadata.

    Args:
        file: The uploaded file (multipart/form-data).

    Returns:
        UploadResponse with document metadata on success.

    Raises:
        HTTPException 400: If the file type is invalid or file is empty.
        HTTPException 500: If the file could not be saved or processed.
    """
    # Log the incoming upload
    logger.info(
        "Upload request: filename=%s, content_type=%s",
        file.filename,
        file.content_type,
    )

    # Validate that a file was actually sent
    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "No file provided",
                "detail": "Please attach a file to upload",
            },
        )

    try:
        # Process the upload through the service layer
        metadata = await upload_service.process_upload(file)

        logger.info(
            "Upload successful: id=%s, size=%s, chars=%s",
            metadata["id"],
            metadata["file_size_display"],
            metadata["text_length"],
        )

        return UploadResponse(
            success=True,
            message=f"File '{file.filename}' uploaded successfully",
            document=metadata,  # type: ignore[arg-type]
        )

    except ValueError as exc:
        # Handle validation errors (bad extension, empty file, too large)
        logger.warning("Upload validation failed: %s", exc)
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": "Invalid file",
                "detail": str(exc),
            },
        )

    except RuntimeError as exc:
        # Handle processing errors (disk write failure, etc.)
        logger.exception("Upload processing failed")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Failed to process upload",
                "detail": str(exc),
            },
        )

    except Exception as exc:
        # Handle unexpected errors
        logger.exception("Unexpected upload error")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error",
                "detail": str(exc),
            },
        )