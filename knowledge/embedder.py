from sentence_transformers import SentenceTransformer
from typing import List
import logging
import time

import torch

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = None):
        self.model_name = model_name

        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            elif torch.backends.mps.is_available():
                self.device = "mps" 
            else:
                self.device = "cpu"
        else:
            self.device = device

        logger.info(f"Loading embedding model: {model_name} on {self.device}")

        try:
            self.model = SentenceTransformer(model_name, device=self.device)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            error_msg = f"Failed to load embedding model '{model_name}': {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def embed(self, text: str) -> List[float]:
        if not isinstance(text, str):
            raise TypeError("Input text must be a string.")
        if text.strip() == "":
            raise ValueError("Input text cannot be empty.")
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()  # Convert to list for easier storage
        except Exception as e:
            error_msg = f"Failed to generate embedding for text: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not isinstance(texts, list):
            raise TypeError("Input must be a list of strings.")
        if len(texts) == 0:
            return []
        
        for i, text in enumerate(texts):
            if not isinstance(text, str):
                raise TypeError(f"All items in the input list must be strings. Item at index {i} is of type {type(text).__name__}.")
            if text.strip() == "":
                raise ValueError(f"Input text at index {i} cannot be empty.")

        start_time = time.time()
        try:
            embeddings = self.model.encode(texts)
        except Exception as e:
            error_msg = f"Failed to generate embeddings for batch: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        
        elapsed_time = time.time() - start_time

        logger.info(f"Generated embeddings for {len(texts)} texts in {elapsed_time:.2f} seconds.")

        return embeddings.tolist()  # Convert to list for easier storage
