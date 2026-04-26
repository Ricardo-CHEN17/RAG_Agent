"""RAG tool adapter that formats retrieval output for agent consumption."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

class RAGTool:
    """Bridge between tool calls and vector-store-based knowledge retrieval."""

    def __init__(self, embedder: Any, vector_store: Any):
        """Store retrieval dependencies used by ``search_knowledge``.

        Args:
            embedder: Embedding dependency injected for future extensibility.
            vector_store: Vector store implementation that provides
                ``similarity_search``.
        """
        self.embedder = embedder
        self.vector_store = vector_store
        logger.info("RAGTool initialized with provided embedder and vector store.")

    def search_knowledge(self, query: str, top_k: int = 3) -> str:
        """Search indexed knowledge and return formatted source-text paragraphs.

        Args:
            query: User query text.
            top_k: Maximum number of relevant chunks to retrieve.

        Returns:
            str: Formatted retrieval text, a no-result notice, or an error
                string beginning with "Error: " for invalid input or failures.
        """
        if not query or not isinstance(query, str):
            return "Error: Invalid query provided."

        try:
            top_k = int(top_k)
        except (TypeError, ValueError):
            return "Error: Invalid top_k provided."

        if top_k <= 0:
            return "Error: top_k must be a positive integer."
        
        try:
            results = self.vector_store.similarity_search(query, top_k=top_k)
        except Exception as e:
            logger.error(f"Failed to search vector store: {e}")
            return f"Error: Failed to search vector store: {e}"
        
        if not results:
            return "No relevant information found."
        
        paragraphs = []
        for result in results:
            source = result.get("metadata", {}).get("source", "unknown source")
            text = result.get("text") or result.get("document") or ""
            paragraph = f"Source: {source}\n{text}"
            paragraphs.append(paragraph)

        formatted_text = "\n\n".join(paragraphs)
        logger.info(f"Search completed with {len(results)} results found.")
        return formatted_text