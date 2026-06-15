"""
Upload service layer.

Handles file upload validation, disk persistence, and text extraction
from PDF, DOCX, and TXT files. Provides document metadata for the API layer.
"""

import io
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from backend.app.config import settings

logger = logging.getLogger(__name__)

# MIME type mapping
MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


class UploadService:
    """
    Service for handling file uploads.

    Validates file types and sizes, saves files to disk,
    and extracts text content from supported formats.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_upload(self, file: UploadFile) -> dict:
        """
        Validate, save, and extract metadata from an uploaded file.

        Args:
            file: The uploaded file from the FastAPI request.

        Returns:
            A dictionary with document metadata including extracted text.

        Raises:
            ValueError: If the file type is not allowed or file is empty.
            RuntimeError: If text extraction fails or file cannot be saved.
        """
        # 1. Validate file extension
        extension = self._get_extension(file.filename)
        self._validate_extension(extension)

        # 2. Read file contents
        raw_bytes = await file.read()
        self._validate_size(raw_bytes, file.filename)

        # 3. Generate a unique filename
        safe_filename = self._generate_filename(file.filename, extension)

        # 4. Extract text content
        text_content = self._extract_text(raw_bytes, extension, file.filename)

        # 5. Save file to disk
        file_path = await self._save_file(raw_bytes, safe_filename)

        # 6. Build metadata
        metadata = self._build_metadata(
            filename=safe_filename,
            original_filename=file.filename or "unknown",
            file_path=str(file_path),
            file_size_bytes=len(raw_bytes),
            extension=extension,
            text_content=text_content,
        )

        logger.info(
            "Uploaded: %s (%s, %s)",
            safe_filename,
            metadata["file_size_display"],
            extension,
        )

        return metadata

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _get_extension(self, filename: Optional[str]) -> str:
        """
        Extract the file extension from a filename.

        Args:
            filename: The original filename.

        Returns:
            Lowercase file extension with dot (e.g., '.pdf').

        Raises:
            ValueError: If filename is None or has no extension.
        """
        if not filename or "." not in filename:
            raise ValueError("File must have a valid extension (e.g., .pdf, .docx, .txt)")

        return f".{filename.rsplit('.', 1)[1].lower()}"

    def _validate_extension(self, extension: str) -> None:
        """
        Check if the file extension is in the allowed set.

        Args:
            extension: The file extension to validate.

        Raises:
            ValueError: If the extension is not allowed.
        """
        if extension not in settings.ALLOWED_EXTENSIONS:
            allowed = ", ".join(sorted(settings.ALLOWED_EXTENSIONS))
            raise ValueError(
                f"Invalid file type '{extension}'. "
                f"Allowed types: {allowed}"
            )

    def _validate_size(self, data: bytes, filename: Optional[str]) -> None:
        """
        Check if the file size is within the allowed limit.

        Args:
            data: The raw file bytes.
            filename: The original filename (for logging).

        Raises:
            ValueError: If the file is empty or exceeds MAX_FILE_SIZE.
        """
        if len(data) == 0:
            raise ValueError(f"Uploaded file is empty: {filename or 'unknown'}")

        if len(data) > settings.MAX_FILE_SIZE_BYTES:
            size_mb = len(data) / (1024 * 1024)
            raise ValueError(
                f"File size ({size_mb:.2f} MB) exceeds the "
                f"maximum allowed size of {settings.MAX_FILE_SIZE_MB} MB"
            )

    # ------------------------------------------------------------------
    # File persistence
    # ------------------------------------------------------------------

    def _generate_filename(self, original: Optional[str], extension: str) -> str:
        """
        Generate a unique filename to prevent collisions.

        Format: upload_{short_uuid}_{original_stem}{extension}

        Args:
            original: The original filename.
            extension: The file extension.

        Returns:
            A unique filename string.
        """
        stem = Path(original or "file").stem.replace(" ", "_")[:40]
        unique_id = uuid.uuid4().hex[:8]
        return f"upload_{unique_id}_{stem}{extension}"

    async def _save_file(self, data: bytes, filename: str) -> Path:
        """
        Write the file bytes to the upload directory.

        Args:
            data: The raw file bytes.
            filename: The unique filename to use on disk.

        Returns:
            The absolute Path to the saved file.

        Raises:
            RuntimeError: If the file cannot be written to disk.
        """
        try:
            upload_dir = settings.upload_path
            file_path = upload_dir / filename

            # Write in chunks to handle large files gracefully
            with open(file_path, "wb") as f:
                f.write(data)

            logger.debug("Saved file to: %s", file_path)
            return file_path

        except OSError as exc:
            logger.exception("Failed to save file: %s", filename)
            raise RuntimeError(
                f"Could not save file to disk: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def _extract_text(
        self, data: bytes, extension: str, filename: Optional[str]
    ) -> str:
        """
        Extract text content from the uploaded file.

        Supports:
            - .txt: UTF-8 decoded text (with fallback)
            - .docx: Extracted via mammoth
            - .pdf: Extracted via PyPDF2 fallback (basic)

        Args:
            data: The raw file bytes.
            extension: The file extension.
            filename: The original filename (for logging).

        Returns:
            Extracted text content as a string.
        """
        try:
            if extension == ".txt":
                return self._extract_txt(data)
            elif extension == ".docx":
                return self._extract_docx(data)
            elif extension == ".pdf":
                return self._extract_pdf(data)
            else:
                return ""
        except Exception as exc:
            logger.warning(
                "Text extraction failed for %s: %s",
                filename or "unknown",
                exc,
            )
            return f"[Text extraction failed: {exc}]"

    def _extract_txt(self, data: bytes) -> str:
        """Decode plain text with UTF-8, falling back to latin-1."""
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1")

    def _extract_docx(self, data: bytes) -> str:
        """
        Extract text from a .docx file using mammoth.

        Returns clean HTML-free plain text.
        """
        import mammoth

        result = mammoth.extract_raw_text(io.BytesIO(data))
        return result.value or ""

    def _extract_pdf(self, data: bytes) -> str:
        """
        Extract text from a .pdf file.

        Uses pypdf (modern PDF library). Falls back gracefully
        if no PDF library is installed.
        """
        text_parts = []

        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(data))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        except ImportError:
            logger.warning(
                "No PDF library available. Install 'pypdf' "
                "for PDF text extraction."
            )
            return "[PDF text extraction requires pypdf]"

        extracted = "\n".join(text_parts).strip()
        return extracted or "[No text could be extracted from this PDF]"

    # ------------------------------------------------------------------
    # Metadata builder
    # ------------------------------------------------------------------

    def _build_metadata(
        self,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size_bytes: int,
        extension: str,
        text_content: str,
    ) -> dict:
        """
        Build a metadata dictionary for the uploaded document.

        Args:
            filename: The unique filename on disk.
            original_filename: The original uploaded filename.
            file_path: The path where the file is stored.
            file_size_bytes: Size of the file in bytes.
            extension: File extension.
            text_content: The extracted text content.

        Returns:
            A dictionary with document metadata.
        """
        text_length = len(text_content)

        return {
            "id": filename,
            "original_filename": original_filename,
            "file_path": file_path,
            "file_size_bytes": file_size_bytes,
            "file_size_display": self._format_size(file_size_bytes),
            "mime_type": MIME_TYPES.get(extension, "application/octet-stream"),
            "extension": extension,
            "text_preview": text_content[:500].strip(),
            "text_length": text_length,
            "page_count": self._estimate_page_count(text_content, extension),
            "uploaded_at": datetime.now().isoformat(),
        }

    def list_uploads(self) -> list[dict]:
        """
        List all uploaded documents from the uploads directory.

        Returns:
            A list of dicts with id, original_filename, file_path,
            file_size_display, extension, and uploaded_at for each file.
        """
        upload_dir = settings.upload_path
        if not upload_dir.exists():
            return []

        documents = []
        for file_path in sorted(upload_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not file_path.is_file():
                continue
            stat = file_path.stat()
            documents.append({
                "id": file_path.name,
                "file_path": str(file_path),
                "file_size_bytes": stat.st_size,
                "file_size_display": self._format_size(stat.st_size),
                "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        return documents

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format byte size into a human-readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.2f} MB"

    @staticmethod
    def _estimate_page_count(text: str, extension: str) -> Optional[int]:
        """
        Estimate document page count.

        - PDF/DOCX: rough estimate based on ~3000 chars per page.
        - TXT: not estimated, returns None.

        Args:
            text: The extracted text content.
            extension: The file extension.

        Returns:
            Estimated page count or None for TXT files.
        """
        if extension in (".pdf", ".docx"):
            return max(1, len(text) // 3000)
        return None


# Singleton instance
upload_service = UploadService()