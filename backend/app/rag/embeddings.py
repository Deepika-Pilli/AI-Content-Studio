"""
Embeddings service using HuggingFace sentence-transformers.

Generates vector embeddings for text chunks using a lightweight
sentence-transformer model. Configured via EMBEDDING_MODEL setting.
"""

import logging
import threading
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
        self._model_lock = threading.Lock()

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
        logger.info("embed_text started (chars=%d)", len(text) if text else 0)
        try:
            if not text or not text.strip():
                logger.warning("Received empty text for embedding")
                return np.zeros(self._dimension, dtype=np.float32)
            logger.info("embed_text validation completed")
        except Exception:
            logger.exception("embed_text validation failed")
            raise

        try:
            logger.info("embed_text acquiring embedding model")
            model = self._get_model()
            logger.info("embed_text acquired embedding model")
        except Exception:
            logger.exception("embed_text failed while acquiring embedding model")
            raise

        try:
            logger.info("embed_text calling SentenceTransformer.encode")
            vector = model.encode(text, normalize_embeddings=True)
            logger.info("embed_text SentenceTransformer.encode completed")
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
        logger.info("embed_batch started (input_count=%d)", len(texts))
        try:
            if not texts:
                logger.info("embed_batch received no texts")
                return []

            logger.info("embed_batch preprocessing started")
            valid_texts = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
            logger.info(
                "embed_batch preprocessing completed (valid_count=%d)",
                len(valid_texts),
            )
            if not valid_texts:
                logger.info("embed_batch has no non-empty texts")
                return [np.zeros(self._dimension, dtype=np.float32) for _ in texts]

            indices, clean_texts = zip(*valid_texts)
        except Exception:
            logger.exception("embed_batch preprocessing failed")
            raise

        try:
            logger.info("embed_batch acquiring embedding model")
            model = self._get_model()
            logger.info("embed_batch acquired embedding model")
        except Exception:
            logger.exception("embed_batch failed while acquiring embedding model")
            raise

        try:
            logger.info(
                "embed_batch calling SentenceTransformer.encode (count=%d)",
                len(clean_texts),
            )
            vectors = model.encode(
                list(clean_texts),
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            logger.info("embed_batch SentenceTransformer.encode completed")
            logger.debug("Embedded batch of %d texts", len(clean_texts))
        except Exception as exc:
            logger.exception("Failed to embed batch of %d texts", len(texts))
            raise RuntimeError(f"Batch embedding failed: {exc}") from exc

        try:
            logger.info("embed_batch rebuilding result vectors")
            result: List[EmbeddingVector] = [
                np.zeros(self._dimension, dtype=np.float32) for _ in texts
            ]
            for idx, vec in zip(indices, vectors):
                result[idx] = np.asarray(vec, dtype=np.float32)
            logger.info("embed_batch completed (output_count=%d)", len(result))
            return result
        except Exception:
            logger.exception("embed_batch result construction failed")
            raise

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    def _get_model(self):
        """
        Lazily load the sentence-transformers model.

        Returns:
            The loaded SentenceTransformer model.
        """
        logger.info("_get_model started (loaded=%s)", self._model is not None)
        lock_acquired = False
        try:
            if self._model is None:
                logger.info("_get_model waiting for model initialization lock")
                with self._model_lock:
                    lock_acquired = True
                    logger.info("_get_model acquired model initialization lock")
                    if self._model is None:
                        logger.info("_get_model initializing model")
                        self._load_model()
                        logger.info("_get_model model initialization completed")
                    else:
                        logger.info("_get_model reusing model initialized by another thread")
            else:
                logger.info("_get_model reusing loaded model")
            return self._model
        except Exception:
            logger.exception("_get_model failed")
            raise
        finally:
            if lock_acquired:
                logger.info("_get_model released model initialization lock")

    def _load_model(self) -> None:
        """
        Load the sentence-transformers model from HuggingFace.

        Uses a lightweight model by default (all-MiniLM-L6-v2, ~80 MB).
        """
        logger.info("_load_model started for: %s", self._model_name)
        try:
            logger.info("_load_model importing SentenceTransformer")
            from sentence_transformers import SentenceTransformer
            logger.info("_load_model imported SentenceTransformer")
        except Exception as exc:
            logger.exception("_load_model failed to import SentenceTransformer")
            raise RuntimeError(
                f"Could not import SentenceTransformer: {exc}"
            ) from exc

        try:
            logger.info("_load_model constructing SentenceTransformer: %s", self._model_name)
            self._model = SentenceTransformer(
                self._model_name,
                trust_remote_code=True,
            )
            logger.info("_load_model constructed SentenceTransformer")
        except Exception as exc:
            logger.exception("_load_model failed to construct SentenceTransformer: %s", self._model_name)
            raise RuntimeError(
                f"Could not load embedding model '{self._model_name}': {exc}"
            ) from exc

        try:
            self._loaded = True
            logger.info("_load_model reading embedding dimension")
            self._dimension = self._model.get_sentence_embedding_dimension()
            logger.info("_load_model read embedding dimension: %d", self._dimension)
            logger.info(
                "Embedding model loaded: %s (dim=%d)",
                self._model_name,
                self._dimension,
            )
        except Exception as exc:
            logger.exception("_load_model failed after constructing model: %s", self._model_name)
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
