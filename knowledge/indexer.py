import os
import hashlib
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class Indexer:
    def __init__(self, vector_store: Any, chunk_size: int = 500, chunk_overlap: int = 50):
        if chunk_overlap >= chunk_size:
            raise ValueError("Chunk overlap must be smaller than chunk size.")

        self.vector_store = vector_store
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        logger.info(f"Indexer initialized with chunk size: {chunk_size} and chunk overlap: {chunk_overlap}")
        
    def _read_text_file(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (FileNotFoundError, UnicodeDecodeError) as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error reading file {file_path}: {e}")
            return ""
        
    def _split_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            logger.debug("No text to split.")
            return []

        chunks = []
        step = self.chunk_size - self.chunk_overlap

        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += step

        logger.debug(f"Text split into {len(chunks)} chunks.")
        return chunks
    
    def index_directory(self, directory_path: str, file_extensions: List[str] = None) -> None:
        if file_extensions is None:
            file_extensions = ['.txt', '.md']
        
        if not os.path.isdir(directory_path):
            raise ValueError(f"Provided path '{directory_path}' is not a valid directory.")
        
        logger.info(f"Indexing directory: {directory_path} with extensions: {file_extensions}")

        all_chunks_to_add = []

        for root, _, files in os.walk(directory_path):
            for file in files:
                if not file.endswith(tuple(file_extensions)):
                    continue

                file_path = os.path.join(root, file)

                text = self._read_text_file(file_path)
                if not text:
                    logger.warning(f"No text extracted from file: {file_path}")
                    continue

                text_chunks = self._split_text(text)
                for i, chunk_text in enumerate(text_chunks):
                    chunk_id = f"{file_path}_chunk_{i}"

                    chunk_dict = {
                        "id": chunk_id,
                        "text": chunk_text,
                        "metadata": {
                            "source": file_path,
                            "chunk_index": i
                        }
                    }
                    all_chunks_to_add.append(chunk_dict)
        
        if all_chunks_to_add:
            logger.info(f"Adding {len(all_chunks_to_add)} chunks to vector store.")
            self.vector_store.add_chunks(all_chunks_to_add)
        else:
            logger.info("No chunks to add to vector store after processing directory.")