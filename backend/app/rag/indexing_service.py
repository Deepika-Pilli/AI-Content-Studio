"""
Indexing service - Orchestrates the full document indexing pipeline.

Coordinates text chunking, embedding generation, and vector storage
to transform an uploaded document into a searchable FAISS index.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.rag.text_splitter import TextSplitterService, text_splitter
from app.rag.embeddings import EmbeddingsService, embeddings_service
from app.rag.vector_store import VectorStoreService

logger = logging.getLogger(__name__)


class IndexingService:
    """
    Orchestrates the document indexing pipeline.

    Steps:
    1. Load document text from a file or text string.
    2. Split text into chunks using TextSplitterService.
    3. Generate embeddings for each chunk using EmbeddingsService.
    4. Store vectors + metadata in a FAISS index via VectorStoreService.
    5. Persist the FAISS index and metadata to disk.
    """

    def __init__(
        self,
        text_splitter_service: Optional[TextSplitterService] = None,
        embeddings_service_instance: Optional[EmbeddingsService] = None,
    ) -> None:
        """
        Initialize the indexing service with its dependencies.

        Args:
            text_splitter_service: Service for chunking text.
            embeddings_service_instance: Service for generating embeddings.
        """
        self.text_splitter = text_splitter_service or text_splitter
        self.embeddings = embeddings_service_instance or embeddings_service

        logger.info("IndexingService initialized")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def index_document(
        self,
        document_id: str,
        text: str,
        source: str = "",
    ) -> dict:
        """
        Index a document's text content end-to-end.

        Args:
            document_id: Unique identifier for the document
                         (used as the FAISS index ID on disk).
            text: The full extracted text content of the document.
            source: Original source identifier (e.g., filename).

        Returns:
            A dictionary with indexing results including chunk count
            and saved file paths.

        Raises:
            ValueError: If the text is empty.
            RuntimeError: If any step in the pipeline fails.
        """
        if not text or not text.strip():
            raise ValueError(
                f"Cannot index document '{document_id}': text content is empty."
            )

        logger.info(
            "Starting indexing pipeline for document: %s (source=%s, chars=%d)",
            document_id,
            source or "unknown",
            len(text),
        )

        # Step 1: Chunk the text
        chunks = self.text_splitter.split_text(text, source=source)
        if not chunks:
            raise RuntimeError(
                f"Text splitting produced zero chunks for document '{document_id}'."
            )

        logger.info("Step 1/3: Split into %d chunks", len(chunks))

        # Step 2: Generate embeddings for all chunks
        chunk_texts = [doc.page_content for doc in chunks]
        vectors = self.embeddings.embed_batch(chunk_texts)
        if not vectors:
            raise RuntimeError(
                f"Embedding generation produced no vectors for '{document_id}'."
            )

        logger.info("Step 2/3: Generated %d embeddings (dim=%d)", len(vectors), vectors[0].shape[0])

        # Step 3: Build metadata for each chunk
        metadata_list = []
        for doc in chunks:
            metadata_list.append(
                {
                    "document_id": document_id,
                    "source": source,
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                    "chunk_size": doc.metadata.get("chunk_size", len(doc.page_content)),
                    "text": doc.page_content,
                }
            )

        # Step 4: Create FAISS index and add vectors
        vector_store = VectorStoreService(dimension=vectors[0].shape[0])
        vector_store.create_index()
        total = vector_store.add_vectors(vectors, metadata_list)

        logger.info("Step 3/3: Stored %d vectors in FAISS index", total)

        # Step 5: Persist to disk
        saved_path = vector_store.save(document_id)

        result = {
            "document_id": document_id,
            "source": source,
            "total_chunks": len(chunks),
            "total_vectors": total,
            "embedding_dimension": vectors[0].shape[0],
            "chunk_size_config": text_splitter.chunk_size,
            "chunk_overlap_config": text_splitter.chunk_overlap,
            "embedding_model": self.embeddings.model_name,
            "saved_to": str(saved_path),
            "index_files": [
                str(saved_path / "index.faiss"),
                str(saved_path / "index.meta"),
            ],
        }

        logger.info(
            "Indexing complete: %d chunks, %d vectors -> %s",
            len(chunks),
            total,
            saved_path,
        )

        return result

    def index_from_file(self, file_path: str, document_id: Optional[str] = None) -> dict:
        """
        Index a document directly from a file on disk.

        Args:
            file_path: Path to the document file.
            document_id: Optional override for the index ID.
                         Defaults to the filename.

        Returns:
            A dictionary with indexing results.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")

        doc_id = document_id or path.name
        text = path.read_text(encoding="utf-8", errors="replace")

        return self.index_document(
            document_id=doc_id,
            text=text,
            source=path.name,
        )


# Singleton instance
indexing_service = IndexingService()