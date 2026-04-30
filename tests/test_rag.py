import os
import pytest
from unittest.mock import MagicMock

from knowledge.vector_store import VectorStore
from knowledge.indexer import Indexer

def test_indexer_chunking(tmp_path):
    mock_vector_store = MagicMock()
    
    indexer = Indexer(vector_store=mock_vector_store, chunk_size=50, chunk_overlap=10)
    
    test_dir = tmp_path / "test_docs"
    test_dir.mkdir()
    test_file = test_dir / "dummy.txt"
    test_file.write_text("Apple is a red fruit. Cars have four wheels." * 10, encoding="utf-8")
    
    indexer.index_directory(str(test_dir))
    
    assert mock_vector_store.add_chunks.called

def test_vector_store_add_and_search(tmp_path):
    mock_embedder = MagicMock()
    mock_embedder.embed_batch.return_value = [[0.1] * 768, [0.2] * 768]
    mock_embedder.embed.return_value = [0.1] * 768
    
    vector_store = VectorStore(persist_dir=str(tmp_path), embedder=mock_embedder)
    
    dummy_chunks = [
        {"id": "chunk_1", "text": "Apple is a red fruit", "metadata": {"source": "fruit.txt"}},
        {"id": "chunk_2", "text": "Cars have four wheels", "metadata": {"source": "car.txt"}}
    ]
    
    vector_store.add_chunks(dummy_chunks)
    
    results = vector_store.similarity_search("Apple", top_k=1)
    
    assert len(results) > 0
    assert "Apple" in results[0]["text"]