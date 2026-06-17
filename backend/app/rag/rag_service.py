"""
RAG (Retrieval-Augmented Generation) query service.

Orchestrates the full pipeline:
1. Retrieve relevant chunks from FAISS index.
2. Build a grounded context from retrieved chunks.
3. Create a prompt with context + user question.
4. Send to Groq LLM for answer generation.
5. Return answer, sources, and similarity scores.
"""

import logging
from typing import List, Optional

from app.config import settings
from app.rag.retrieval_service import RetrievalService, SearchResult, retrieval_service
from app.services.groq_service import GroqService

logger = logging.getLogger(__name__)

# Default number of chunks to retrieve for RAG context
DEFAULT_RAG_TOP_K = 5


class RagService:
    """
    RAG query service.

    Combines document retrieval with LLM generation to produce
    grounded answers based on indexed document content.
    """

    def __init__(
        self,
        retrieval: Optional[RetrievalService] = None,
        groq: Optional[GroqService] = None,
    ) -> None:
        """
        Initialise the RAG service.

        Args:
            retrieval: Service for retrieving relevant chunks.
                       Defaults to the singleton RetrievalService.
            groq: Service for LLM generation.
                  Defaults to a new GroqService instance.
        """
        self.retrieval = retrieval or retrieval_service
        self.groq = groq or GroqService()
        logger.info("RagService initialised")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query(
        self,
        document_id: str,
        question: str,
        top_k: int = DEFAULT_RAG_TOP_K,
    ) -> dict:
        """
        Execute a full RAG query: retrieve → context → generate.

        Args:
            document_id: The indexed document to search.
            question: The user's question.
            top_k: Number of chunks to retrieve for context (1-10).

        Returns:
            A dictionary containing:
                - success: Whether the query succeeded.
                - answer: The generated answer text.
                - question: The original question.
                - document_id: The document that was searched.
                - retrieved_chunks: List of chunks used as context.
                - total_chunks_retrieved: Count of chunks.
                - model: The LLM model used for generation.

        Raises:
            ValueError: If question is empty.
            FileNotFoundError: If the document index doesn't exist.
            RuntimeError: If retrieval or generation fails.
        """
        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        # Step 1: Retrieve relevant chunks
        logger.info(
            "RAG query: document=%s, question=%.60s..., top_k=%d",
            document_id,
            question,
            top_k,
        )

        results = self.retrieval.retrieve(
            document_id=document_id,
            query=question,
            top_k=top_k,
        )

        if not results:
            raise RuntimeError(
                f"No relevant chunks found for question in document '{document_id}'."
            )

        # Step 2: Build context from retrieved chunks
        context = self._build_context(results)
        logger.info(
            "Built context from %d chunks (%d total chars)",
            len(results),
            len(context),
        )

        # Step 3: Build the grounded prompt
        prompt = self._build_prompt(question, context)
        logger.debug("Prompt built (%d chars)", len(prompt))

        # Step 4: Generate answer via Groq
        try:
            generation_result = self.groq.generate_sync(
                prompt=prompt,
                content_type="general",
                tone="professional",
                max_tokens=1024,
                temperature=0.3,  # Lower temperature for factual answers
            )
        except RuntimeError as exc:
            logger.exception("Groq generation failed for RAG query")
            raise RuntimeError(f"Answer generation failed: {exc}") from exc

        answer = generation_result.get("content", "")
        model = generation_result.get("model", settings.GROQ_MODEL)

        # Step 5: Build response
        chunk_list = []
        for r in results:
            chunk_list.append(r.to_dict())

        response = {
            "success": True,
            "answer": answer,
            "question": question,
            "document_id": document_id,
            "retrieved_chunks": chunk_list,
            "total_chunks_retrieved": len(chunk_list),
            "model": model,
        }

        logger.info(
            "RAG query complete: answer=%d chars, %d chunks, model=%s",
            len(answer),
            len(chunk_list),
            model,
        )

        return response

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context(results: List[SearchResult]) -> str:
        """
        Build a consolidated context string from retrieved chunks.

        Each chunk is prefixed with a source tag for attribution.

        Args:
            results: The list of retrieved SearchResult objects.

        Returns:
            A formatted context string combining all chunks.
        """
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {i} (relevance: {result.score:.2f})]\n{result.text.strip()}"
            )

        return "\n\n---\n\n".join(context_parts)

    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        """
        Build a grounded question-answering prompt.

        Instructs the LLM to answer based solely on the provided
        context and to cite sources when possible.

        Args:
            question: The user's original question.
            context: The consolidated context string from chunks.

        Returns:
            A formatted prompt string for the LLM.
        """
        return (
            "You are a helpful AI assistant that answers questions based on provided context.\n\n"
            "INSTRUCTIONS:\n"
            "1. Answer the question using ONLY the context provided below.\n"
            "2. If the context does not contain enough information to answer, "
            "say 'I cannot find sufficient information in the document to answer this question.'\n"
            "3. Cite the relevant source numbers (e.g., [Source 1]) when referencing specific information.\n"
            "4. Be concise, accurate, and professional.\n"
            "5. Do not make up information or use external knowledge.\n\n"
            "--- CONTEXT ---\n"
            f"{context}\n"
            "--- END OF CONTEXT ---\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )


# Singleton instance
rag_service = RagService()