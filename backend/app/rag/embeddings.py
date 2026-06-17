"""
Embeddings service using HuggingFace sentence-transformers.

Generates vector embeddings for text chunks using a lightweight
sentence-transformer model. Configured via EMBEDDING_MODEL setting.
"""

import logging
from typing import List, Optional

import numpy as np
from numpy.typing import NDArray

from app.config import settings

logger = logging.getLogger(__name__)

# Type alias for embedding vectors
EmbeddingVector = NDArray[np.float32]


class EmbeddingsService:
    """
    Service for generating text embeddings using HuggingFace models.

    Uses sentence-transformers for efficient, high-quality embeddings
    suitable for semantic search and clustering.
    """

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL) -> None:
        """
        Initialize the embedding model.

        The model is loaded lazily on first use to avoid blocking
        application startup.

        Args:
            model_name: HuggingFace model identifier for sentence-transformers.
        """
        self._model_name = model_name
        self._model = None
        self._dimension = settings.EMBEDDING_DIMENSION
        self._loaded = False

        logger.info(
            "EmbeddingsService configured: model=%s, dim=%d",
            model_name,
            self._dimension,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> EmbeddingVector:
        """
        Generate an embedding vector for a single text string.

        Args:
            text: The text to embed.

        Returns:
            A numpy array of floats representing the embedding.

        Raises:
            RuntimeError: If the model fails to load or encode.
        """
        if not text or not text.strip():
            logger.warning("Received empty text for embedding")
            return np.zeros(self._dimension, dtype=np.float32)

        model = self._get_model()
        try:
            vector = model.encode(text, normalize_embeddings=True)
            logger.debug("Embedded %d chars -> vector of length %d", len(text), len(vector))
            return np.asarray(vector, dtype=np.float32)
        except Exception as exc:
            logger.exception("Failed to embed text")
            raise RuntimeError(f"Embedding failed: {exc}") from exc

    def embed_batch(self, texts: List[str]) -> List[EmbeddingVector]:
        """
        Generate embedding vectors for a batch of text strings.

        Batch processing is more efficient than calling embed_text
        repeatedly, as it leverages GPU/CPU parallelism.

        Args:
            texts: A list of text strings to embed.

        Returns:
            A list of numpy arrays, one per input text.
        """
        if not texts:
            return []

        # Filter empty texts
        valid_texts = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
        if not valid_texts:
            return [np.zeros(self._dimension, dtype=np.float32) for _ in texts]

        indices, clean_texts = zip(*valid_texts)

        model = self._get_model()
        try:
            vectors = model.encode(
                list(clean_texts),
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            logger.debug("Embedded batch of %d texts", len(clean_texts))

            # Rebuild full result list with zeros for empty inputs
            result: List[EmbeddingVector] = [
                np.zeros(self._dimension, dtype=np.float32) for _ in texts
            ]
            for idx, vec in zip(indices, vectors):
                result[idx] = np.asarray(vec, dtype=np.float32)

            return result

        except Exception as exc:
            logger.exception("Failed to embed batch of %d texts", len(texts))
            raise RuntimeError(f"Batch embedding failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    def _get_model(self):
        """
        Lazily load the sentence-transformers model.

        Returns:
            The loaded SentenceTransformer model.
        """
        if self._model is None:
            self._load_model()
        return self._model

    def _load_model(self) -> None:
        """
        Load the sentence-transformers model from HuggingFace.

        Uses a lightweight model by default (all-MiniLM-L6-v2, ~80 MB).
        """
        try:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading embedding model: %s ...", self._model_name)
            self._model = SentenceTransformer(
                self._model_name,
                trust_remote_code=True,
            )
            self._loaded = True
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info(
                "Embedding model loaded: %s (dim=%d)",
                self._model_name,
                self._dimension,
            )
        except Exception as exc:
            logger.exception("Failed to load embedding model: %s", self._model_name)
            raise RuntimeError(
                f"Could not load embedding model '{self._model_name}': {exc}"
            ) from exc

    @property
    def is_loaded(self) -> bool:
        """Check if the embedding model is loaded and ready."""
        return self._loaded

    @property
    def model_name(self) -> str:
        """Get the configured model name."""
        return self._model_name

    @property
    def dimension(self) -> int:
        """Get the embedding vector dimension."""
        return self._dimension


# Singleton instance
embeddings_service = EmbeddingsService()