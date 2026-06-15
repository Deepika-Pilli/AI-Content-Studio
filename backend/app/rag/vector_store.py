"""
Vector store service using FAISS.

Manages FAISS index creation, vector addition, persistence to disk,
and loading from disk. Stores chunk metadata alongside vectors for
future retrieval.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import faiss
from numpy.typing import NDArray

from backend.app.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """
    Service for managing a FAISS vector index.

    Handles:
    - Creating a new FAISS index with the correct dimension.
    - Adding embedding vectors with associated metadata.
    - Persisting the index and metadata to disk.
    - Loading a previously saved index from disk.
    """

    def __init__(self, dimension: int = settings.EMBEDDING_DIMENSION) -> None:
        """
        Initialize the vector store service.

        Args:
            dimension: The dimensionality of embedding vectors.
                       Must match the embedding model's output dimension.
        """
        self._dimension = dimension
        self._index: Optional[faiss.Index] = None
        self._metadata: List[Dict[str, Any]] = []
        self._total_vectors: int = 0

        logger.info("VectorStoreService initialized (dim=%d)", dimension)

    # ------------------------------------------------------------------
    # Index lifecycle
    # ------------------------------------------------------------------

    def create_index(self, dimension: Optional[int] = None) -> None:
        """
        Create a new FAISS index.

        Uses IndexFlatIP (inner product) for exact search with
        cosine similarity (vectors are normalized).

        Args:
            dimension: Optional override for vector dimension.
                       Defaults to the configured embedding dimension.
        """
        dim = dimension or self._dimension
        self._index = faiss.IndexFlatIP(dim)
        self._metadata = []
        self._total_vectors = 0

        logger.info("Created new FAISS index (dim=%d, type=%s)", dim, type(self._index).__name__)

    def add_vectors(
        self,
        vectors: List[NDArray[np.float32]],
        metadata_list: List[Dict[str, Any]],
    ) -> int:
        """
        Add vectors and their metadata to the index.

        Args:
            vectors: A list of numpy embedding vectors.
            metadata_list: A list of metadata dicts, one per vector.
                           Must be the same length as vectors.

        Returns:
            The total number of vectors in the index after addition.

        Raises:
            RuntimeError: If the index hasn't been created.
            ValueError: If vectors and metadata lengths don't match.
        """
        if self._index is None:
            raise RuntimeError(
                "FAISS index has not been created. Call create_index() first."
            )

        if len(vectors) != len(metadata_list):
            raise ValueError(
                f"Vector count ({len(vectors)}) must match "
                f"metadata count ({len(metadata_list)})"
            )

        if not vectors:
            logger.warning("No vectors to add")
            return self._total_vectors

        # Convert to float32 numpy array (FAISS requirement)
        vector_array = np.asarray(vectors, dtype=np.float32)
        if vector_array.ndim == 1:
            vector_array = vector_array.reshape(1, -1)

        # Add to index
        self._index.add(vector_array)
        self._metadata.extend(metadata_list)
        self._total_vectors = self._index.ntotal

        logger.info(
            "Added %d vectors to index (total: %d)",
            len(vectors),
            self._total_vectors,
        )

        return self._total_vectors

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, index_id: str) -> Path:
        """
        Save the FAISS index and metadata to disk.

        Creates a subdirectory named after the index_id in the vectors directory.
        Two files are saved:
          - {index_id}.faiss : The FAISS binary index
          - {index_id}.meta  : JSON-serialised metadata list

        Args:
            index_id: A unique identifier for the index (e.g., document filename).

        Returns:
            The Path to the saved index subdirectory.

        Raises:
            RuntimeError: If the index hasn't been created or is empty.
        """
        if self._index is None:
            raise RuntimeError("Cannot save: FAISS index has not been created.")
        if self._total_vectors == 0:
            raise RuntimeError("Cannot save: FAISS index is empty.")

        vectors_dir = settings.vectors_path
        index_dir = vectors_dir / self._sanitise_id(index_id)
        index_dir.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = index_dir / "index.faiss"
        faiss.write_index(self._index, str(index_path))

        # Save metadata as JSON
        meta_path = index_dir / "index.meta"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "index_id": index_id,
                    "dimension": self._dimension,
                    "total_vectors": self._total_vectors,
                    "metadata": self._metadata,
                    "config": {
                        "embedding_model": settings.EMBEDDING_MODEL,
                    },
                },
                f,
                indent=2,
                default=str,
            )

        logger.info(
            "Saved FAISS index to %s (%d vectors, %s)",
            index_dir,
            self._total_vectors,
            index_path,
        )

        return index_dir

    def load(self, index_id: str) -> bool:
        """
        Load a previously saved FAISS index from disk.

        Args:
            index_id: The unique identifier used when saving.

        Returns:
            True if the index was loaded successfully, False otherwise.

        Raises:
            RuntimeError: If the index files are corrupted.
        """
        vectors_dir = settings.vectors_path
        index_dir = vectors_dir / self._sanitise_id(index_id)
        index_path = index_dir / "index.faiss"
        meta_path = index_dir / "index.meta"

        if not index_path.exists() or not meta_path.exists():
            logger.warning(
                "Saved index not found at %s", index_dir
            )
            return False

        try:
            # Load FAISS index
            self._index = faiss.read_index(str(index_path))

            # Load metadata
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._metadata = data.get("metadata", [])
            self._total_vectors = data.get("total_vectors", 0)
            self._dimension = data.get("dimension", self._dimension)

            logger.info(
                "Loaded FAISS index from %s (%d vectors, dim=%d)",
                index_dir,
                self._total_vectors,
                self._dimension,
            )
            return True

        except (OSError, json.JSONDecodeError, RuntimeError) as exc:
            logger.exception("Failed to load FAISS index: %s", index_dir)
            raise RuntimeError(f"Could not load index '{index_id}': {exc}") from exc

    def exists(self, index_id: str) -> bool:
        """Check if a saved index exists on disk."""
        vectors_dir = settings.vectors_path
        index_dir = vectors_dir / self._sanitise_id(index_id)
        return (index_dir / "index.faiss").exists()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def index(self) -> Optional[faiss.Index]:
        """Get the underlying FAISS index."""
        return self._index

    @property
    def metadata(self) -> List[Dict[str, Any]]:
        """Get all stored metadata entries."""
        return self._metadata

    @property
    def total_vectors(self) -> int:
        """Get the total number of vectors in the index."""
        return self._total_vectors

    @property
    def dimension(self) -> int:
        """Get the vector dimension."""
        return self._dimension

    @property
    def is_loaded(self) -> bool:
        """Check if an index has been initialised."""
        return self._index is not None

    def list_indexes(self) -> list[dict]:
        """
        List all indexed documents from the vectors directory.

        Reads index.meta for each saved index to extract
        document_id, total_chunks, and total_vectors.

        Returns:
            A list of dicts with document_id, total_chunks,
            total_vectors, embedding_model, and dimension.
        """
        vectors_dir = settings.vectors_path
        if not vectors_dir.exists():
            return []

        indexes = []
        for entry in sorted(vectors_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not entry.is_dir():
                continue
            meta_path = entry / "index.meta"
            if not meta_path.exists():
                continue
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                indexes.append({
                    "document_id": data.get("index_id", entry.name),
                    "total_chunks": len(data.get("metadata", [])),
                    "total_vectors": data.get("total_vectors", 0),
                    "embedding_model": data.get("config", {}).get("embedding_model", ""),
                    "dimension": data.get("dimension", 0),
                })
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Skipping corrupt index %s: %s", entry.name, exc)
                continue
        return indexes

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitise_id(index_id: str) -> str:
        """
        Sanitise an index ID for use as a directory name.

        Replaces path-unfriendly characters with underscores.
        """
        safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in index_id)
        return safe.strip().replace(" ", "_")
