"""
Text chunking service using LangChain's RecursiveCharacterTextSplitter.

Splits document text into overlapping chunks for embedding and indexing.
Configuration is driven by application settings (CHUNK_SIZE, CHUNK_OVERLAP).
"""

import logging
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from app.config import settings

logger = logging.getLogger(__name__)


class TextSplitterService:
    """
    Service for splitting document text into chunks.

    Uses RecursiveCharacterTextSplitter with sensible defaults,
    configurable via CHUNK_SIZE and CHUNK_OVERLAP environment variables.
    """

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ) -> None:
        """
        Initialize the text splitter with configurable chunk parameters.

        Args:
            chunk_size: Maximum number of characters per chunk.
            chunk_overlap: Number of overlapping characters between chunks.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        )

        logger.info(
            "TextSplitter initialized: chunk_size=%d, overlap=%d",
            chunk_size,
            chunk_overlap,
        )

    def split_text(self, text: str, source: str = "") -> List[Document]:
        """
        Split a plain text string into LangChain Document chunks.

        Each chunk includes source metadata for provenance tracking.

        Args:
            text: The full text content to split.
            source: Optional source identifier (e.g., document filename).

        Returns:
            A list of LangChain Document objects, each containing
            a chunk of text and metadata.
        """
        if not text or not text.strip():
            logger.warning("Received empty text for splitting (source=%s)", source)
            return []

        documents = self._splitter.create_documents(
            texts=[text],
            metadatas=[{"source": source}] if source else None,
        )

        # Add chunk index metadata for ordering
        for i, doc in enumerate(documents):
            doc.metadata["chunk_index"] = i
            doc.metadata["chunk_size"] = len(doc.page_content)

        logger.info(
            "Split text into %d chunks (source=%s, avg_chars=%.0f)",
            len(documents),
            source or "unknown",
            (
                sum(len(d.page_content) for d in documents) / max(len(documents), 1)
            ),
        )

        return documents

    def split_text_to_dicts(self, text: str, source: str = "") -> List[dict]:
        """
        Split text and return chunks as plain dictionaries.

        Convenience method for simpler serialization.

        Args:
            text: The full text content to split.
            source: Optional source identifier.

        Returns:
            A list of dicts with 'text' and 'metadata' keys.
        """
        docs = self.split_text(text, source=source)
        return [
            {
                "text": doc.page_content,
                "metadata": doc.metadata,
            }
            for doc in docs
        ]

    @property
    def config(self) -> dict:
        """Return current chunking configuration."""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }


# Singleton instance
text_splitter = TextSplitterService()