"""
Pydantic models for document upload and metadata.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """
    Metadata about an uploaded document.

    Attributes:
        id: Unique identifier for the document (filename).
        original_filename: The original name of the uploaded file.
        file_path: Relative path where the file is stored on disk.
        file_size_bytes: Size of the file in bytes.
        file_size_display: Human-readable file size string.
        mime_type: The MIME type of the file.
        extension: File extension (e.g., .pdf, .docx, .txt).
        text_preview: First 500 characters of extracted text content.
        text_length: Total length of extracted text in characters.
        page_count: Approximate page count (estimated for TXT).
        uploaded_at: Timestamp when the file was uploaded.
    """

    id: str = Field(
        ...,
        description="Unique identifier (filename on disk)",
        example="doc_abc123_linkedin_post.pdf",
    )
    original_filename: str = Field(
        ...,
        description="Original name of the uploaded file",
        example="linkedin_post.pdf",
    )
    file_path: str = Field(
        ...,
        description="Relative path on disk",
        example="backend/uploads/doc_abc123_linkedin_post.pdf",
    )
    file_size_bytes: int = Field(
        ...,
        description="File size in bytes",
        example=245760,
    )
    file_size_display: str = Field(
        ...,
        description="Human-readable file size",
        example="240.00 KB",
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the file",
        example="application/pdf",
    )
    extension: str = Field(
        ...,
        description="File extension",
        example=".pdf",
    )
    text_preview: str = Field(
        ...,
        description="First 500 characters of extracted text",
        example="Artificial intelligence is transforming...",
    )
    text_length: int = Field(
        ...,
        description="Total length of extracted text in characters",
        example=12500,
    )
    page_count: Optional[int] = Field(
        default=None,
        description="Approximate page count",
        example=5,
    )
    uploaded_at: str = Field(
        ...,
        description="ISO 8601 upload timestamp",
        example="2026-06-12T21:30:00.000000",
    )


class UploadResponse(BaseModel):
    """
    Response returned after a successful file upload.

    Attributes:
        success: Whether the upload was successful.
        message: Human-readable success message.
        document: Metadata about the uploaded document.
    """

    success: bool = Field(
        default=True,
        description="Whether the upload was successful",
    )
    message: str = Field(
        ...,
        description="Human-readable success message",
        example="File uploaded successfully",
    )
    document: DocumentMetadata = Field(
        ...,
        description="Metadata about the uploaded document",
    )


class UploadErrorResponse(BaseModel):
    """
    Error response for failed uploads.

    Attributes:
        success: Always False for errors.
        error: Error message describing what went wrong.
        detail: Optional detailed error information.
    """

    success: bool = Field(
        default=False,
        description="Always False for errors",
    )
    error: str = Field(
        ...,
        description="Error message",
        example="Invalid file type",
    )
    detail: Optional[str] = Field(
        default=None,
        description="Detailed error information",
        example="Allowed types: .pdf, .docx, .txt",
    )