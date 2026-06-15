"""
RAG (Retrieval-Augmented Generation) package.

Provides text chunking, embedding generation, and vector storage
using LangChain, HuggingFace, and FAISS. This is the foundation
for future document retrieval and question-answering features.
"""

from .text_splitter import TextSplitterService
from .embeddings import EmbeddingsService
from .vector_store import VectorStoreService
from .indexing_service import IndexingService
from .retrieval_service import RetrievalService, SearchResult, retrieval_service
from .rag_service import RagService, rag_service

__all__ = [
    "TextSplitterService",
    "EmbeddingsService",
    "VectorStoreService",
    "IndexingService",
    "RetrievalService",
    "SearchResult",
    "retrieval_service",
    "RagService",
    "rag_service",
]
