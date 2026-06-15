"""
Retrieval service for searching a FAISS index.

Loads a previously persisted FAISS index from disk, embeds a user
query using the same HuggingFace model, and returns the top-k most
similar chunks with metadata and similarity scores.
"""

import logging
from typing import List, Optional

import numpy as np

from backend.app.config import settings
from backend.app.rag.embeddings import EmbeddingsService, embeddings_service
from backend.app.rag.vector_store import VectorStoreService

logger = logging.getLogger(__name__)

# Default number of results to return
DEFAULT_TOP_K = 5
MAX_TOP_K = 50


class SearchResult:
    """
    A single search result from a retrieval query.

    Attributes:
        chunk_index: Index of the chunk within the document.
        text: The chunk text content.
        source: Source document identifier.
        document_id: The document this chunk belongs to.
        score: Cosine similarity score (higher = more similar).
        chunk_size: Number of characters in the chunk.
    """

    def __init__(
        self,
        chunk_index: int,
        text: str,
        source: str,
        document_id: str,
        score: float,
        chunk_size: int,
    ) -> None:
        self.chunk_index = chunk_index
        self.text = text
        self.source = source
        self.document_id = document_id
        self.score = float(score)
        self.chunk_size = chunk_size

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialisation."""
        return {
            "chunk_index": self.chunk_index,
            "text": self.text,
            "source": self.source,
            "document_id": self.document_id,
            "score": round(self.score, 4),
            "chunk_size": self.chunk_size,
        }

    def __repr__(self) -> str:
        return (
            f"SearchResult(idx={self.chunk_index}, "
            f"score={self.score:.4f}, source={self.source})"
        )


class RetrievalService:
    """
    Service for retrieving relevant document chunks from a FAISS index.

    Steps:
    1. Load FAISS index + metadata for a given document_id.
    2. Embed the user query using the same embedding model.
    3. Search the FAISS index for the top-k most similar vectors.
    4. Return chunk text, metadata, and similarity scores.
    """

    def __init__(
        self,
        embeddings_service_instance: Optional[EmbeddingsService] = None,
    ) -> None:
        """
        Initialise the retrieval service.

        Args:
            embeddings_service_instance: Service for embedding queries.
                                         Defaults to the singleton.
        """
        self.embeddings = embeddings_service_instance or embeddings_service
        logger.info("RetrievalService initialised")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        document_id: str,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[SearchResult]:
        """
        Retrieve the top-k most relevant chunks for a query.

        Args:
            document_id: The identifier of the document index to search.
            query: The user's search query.
            top_k: Number of results to return (1-50, default 5).

        Returns:
            A list of SearchResult objects, ordered by relevance
            (highest score first).

        Raises:
            ValueError: If query is empty or top_k is out of range.
            FileNotFoundError: If no index exists for the given document_id.
            RuntimeError: If the FAISS index fails to load or search.
        """
        # 1. Validate inputs
        self._validate_query(query)
        self._validate_top_k(top_k)

        # 2. Load the FAISS index from disk
        vector_store = VectorStoreService()
        loaded = vector_store.load(document_id)
        if not loaded:
            raise FileNotFoundError(
                f"No FAISS index found for document '{document_id}'. "
                f"Ensure the document has been indexed via POST /index/ first."
            )

        # Sanity check dimension
        if vector_store.total_vectors == 0:
            raise RuntimeError(
                f"FAISS index for '{document_id}' is empty (0 vectors)."
            )

        logger.info(
            "Loaded index '%s': %d vectors, dim=%d",
            document_id,
            vector_store.total_vectors,
            vector_store.dimension,
        )

        # 3. Embed the query
        query_vector = self.embeddings.embed_text(query)
        logger.debug(
            "Query embedded: dim=%d, norm=%.4f",
            len(query_vector),
            np.linalg.norm(query_vector),
        )

        # 4. Search the index
        try:
            # FAISS search returns (distances, indices)
            distances, indices = vector_store.index.search(
                query_vector.reshape(1, -1).astype(np.float32),
                min(top_k, vector_store.total_vectors),
            )
        except Exception as exc:
            logger.exception("FAISS search failed for query: %.50s", query)
            raise RuntimeError(f"FAISS search failed: {exc}") from exc

        # 5. Build result objects
        results: List[SearchResult] = []
        metadata_list = vector_store.metadata

        for rank in range(len(indices[0])):
            idx = int(indices[0][rank])

            # FAISS may return -1 for empty slots
            if idx == -1 or idx >= len(metadata_list):
                continue

            meta = metadata_list[idx]
            score = float(distances[0][rank])

            result = SearchResult(
                chunk_index=meta.get("chunk_index", idx),
                text=meta.get("text", ""),
                source=meta.get("source", ""),
                document_id=meta.get("document_id", document_id),
                score=score,
                chunk_size=meta.get("chunk_size", 0),
            )
            results.append(result)

        logger.info(
            "Retrieved %d results for query (%.50s...) from '%s'",
            len(results),
            query,
            document_id,
        )
        return results

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_query(query: str) -> None:
        """Ensure the query is non-empty."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty. Please provide a search query.")

    @staticmethod
    def _validate_top_k(top_k: int) -> None:
        """Ensure top_k is within allowed range."""
        if top_k < 1:
            raise ValueError(f"top_k must be at least 1, got {top_k}.")
        if top_k > MAX_TOP_K:
            raise ValueError(
                f"top_k cannot exceed {MAX_TOP_K}, got {top_k}."
            )


# Singleton instance
retrieval_service = RetrievalService()