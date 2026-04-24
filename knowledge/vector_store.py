import chromadb
from chromadb import PersistentClient
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class VectorStore:
    """ChromaDB-backed vector storage for document chunks and retrieval."""

    def __init__(self, persist_dir: str, embedder: Any, collection_name: str = "doc_chunks"):
        """Initialize persistent client and target collection."""
        self.persist_dir = persist_dir
        self.embedder = embedder

        logger.info(f"Initializing VectorStore with persist directory: {persist_dir}")

        try:
            self.client = self.client = PersistentClient(path=persist_dir)
            self.collection = self.client.get_or_create_collection(name=collection_name)
            logger.info(f"VectorStore initialized successfully with collection: {collection_name}")
        except Exception as e:
            error_msg = f"Failed to initialize VectorStore: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Embed and store chunk payloads in the configured collection."""
        if not chunks:
            logger.warning("No chunks to add to the vector store.")
            return
        
        logger.info(f"Preparing to add {len(chunks)} chunks to VectorStore...")

        try:
            # Keep IDs, metadata, and source text aligned with embedding order.
            texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedder.embed_batch(texts)
            ids = [chunk["id"] for chunk in chunks]
            metadatas = [chunk.get("metadata", {}) for chunk in chunks]

            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=texts
            )
            logger.info(f"Successfully added {len(chunks)} chunks to VectorStore.")
        except Exception as e:
            error_msg = f"Failed to add chunks to VectorStore: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        
    def similarity_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Return top-k closest chunks for a query using embedding similarity."""
        if not isinstance(query, str) or query.strip() == "":
            raise ValueError("Query must be a non-empty string.")
        if top_k <= 0:
            raise ValueError("top_k must be a positive integer.")
        
        logger.info(f"Performing similarity search for query: '{query}' with top_k={top_k}")

        try:
            query_vector = self.embedder.embed(query)
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
            )

            # Normalize Chroma's nested response to a flat list of result dicts.
            formatted_results = []

            if not results["ids"] or not results["ids"][0]:
                return formatted_results
            
            for i in range(len(results["ids"][0])):
                doc_item = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                }
                formatted_results.append(doc_item)

            return formatted_results
        
        except Exception as e:
            error_msg = f"Failed to perform similarity search: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e