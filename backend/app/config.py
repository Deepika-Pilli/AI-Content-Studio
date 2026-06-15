"""
Application configuration module.

Loads environment variables and provides typed settings
for the AI Content Studio backend.
"""

import os
from typing import Set
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend/ directory (always relative to this file, not CWD)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # API Authentication
    API_KEY: str = os.getenv("API_KEY", "dev-key-change-in-production")

    # Groq API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Server
    APP_TITLE: str = "AI Content Studio"
    APP_VERSION: str = "1.0.0"

    # Upload
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "backend/uploads")
    VECTOR_DIR: str = os.getenv("VECTOR_DIR", "backend/vectors")

    # File upload constraints
    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx", ".txt"}
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

    # Embeddings
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    EMBEDDING_DIMENSION: int = 384  # all-MiniLM-L6-v2 output dimension

    @property
    def is_groq_configured(self) -> bool:
        """Check if Groq API key is available."""
        return bool(self.GROQ_API_KEY)

    @property
    def upload_path(self) -> Path:
        """Get the upload directory as a Path object, ensuring it exists."""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def vectors_path(self) -> Path:
        """Get the vectors directory as a Path object, ensuring it exists."""
        path = Path(self.VECTOR_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
