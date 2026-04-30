import os
import pytest
from tools.file_tools import FileTools

@pytest.fixture
def file_tools():
    return FileTools()

def test_list_files_success(file_tools, tmp_path):

    test_file = tmp_path / "dummy_doc.txt"
    test_file.write_text("Hello World")

    result = file_tools.list_files(str(tmp_path))

    assert "dummy_doc.txt" in result

def test_list_files_not_found(file_tools):

    result = file_tools.list_files("/non/existent/directory")
    assert "Error" in result

def test_read_file_success(file_tools, tmp_path):

    test_file = tmp_path / "dummy_doc.txt"
    content = "Test content for read_file."
    test_file.write_text(content)

    result = file_tools.read_file(str(test_file))
    assert result == content

def test_read_file_truncate(file_tools, tmp_path):

    test_file = tmp_path / "large_file.txt"
    content = "A" * 15000
    test_file.write_text(content)

    result = file_tools.read_file(str(test_file), max_chars=10000)
    assert result.startswith("A" * 10000)

from unittest.mock import MagicMock
from tools.rag_tool import RAGTool

def test_search_knowledge_empty():
    mock_vector_store = MagicMock()
    mock_embedder = MagicMock()

    mock_vector_store.similarity_search.return_value = []

    rag_tool = RAGTool(embedder=mock_embedder, vector_store=mock_vector_store)

    result = rag_tool.search_knowledge("test query")
    assert "No relevant" in result 

def test_search_knowledge_success():
    mock_vector_store = MagicMock()
    mock_embedder = MagicMock()

    mock_vector_store.similarity_search.return_value = [{"metadata": {"source": "test_doc.txt"}, "text": "Relevant result 1"},
                                                         {"metadata": {"source": "test_doc.txt"}, "text": "Relevant result 2"}]

    rag_tool = RAGTool(embedder=mock_embedder, vector_store=mock_vector_store)

    result = rag_tool.search_knowledge("test query")
    assert "Relevant result 1" in result
    assert "Relevant result 2" in result