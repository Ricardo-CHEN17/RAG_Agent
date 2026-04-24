import logging
from typing import Any

logger = logging.getLogger(__name__)

class RAGTool:
    def __init__(self, embedder: Any, vector_store: Any):
        self.embedder = embedder
        self.vector_store = vector_store
        logger.info("RAGTool initialized with provided embedder and vector store.")

    def search_knowledge(self, query: str, top_k: int = 3) -> str:
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