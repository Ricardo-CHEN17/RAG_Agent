import pytest
from unittest.mock import MagicMock
from agent.controller import AgentController

def test_controller_direct_answer():
    mock_client = MagicMock()
    mock_executor = MagicMock()

    mock_client.chat.return_value = {
        "message": {
            "content": "I am a local AI assistant.",
            "tool_calls": None
        }
    }

    controller = AgentController(model_client=mock_client, tool_executor=mock_executor, max_iterations=5)
    result = controller.run("Who are you?")

    assert result == "I am a local AI assistant."
    assert not mock_executor.execute.called

def test_controller_with_tool_call():
    mock_client = MagicMock()
    mock_executor = MagicMock()

    mock_client.chat.side_effect = [
        {
            "message": {
                "content": "",
                "tool_calls": [{"function": {"name": "search_knowledge", "arguments": {"query": "apple"}}}]
            }
        },
        {
            "message": {
                "content": "Based on the data, an apple is a red fruit.",
                "tool_calls": None
            }
        }
    ]

    mock_executor.execute.return_value = "Search result: Apple is red."

    controller = AgentController(model_client=mock_client, tool_executor=mock_executor, max_iterations=5)
    result = controller.run("What is an apple?")

    assert result == "Based on the data, an apple is a red fruit."
    assert mock_executor.execute.called
    assert mock_client.chat.call_count == 2

def test_controller_timeout():
    mock_client = MagicMock()
    mock_executor = MagicMock()

    mock_client.chat.return_value = {
        "message": {
            "content": "",
            "tool_calls": [{"function": {"name": "read_file", "arguments": {}}}]
        }
    }

    controller = AgentController(model_client=mock_client, tool_executor=mock_executor, max_iterations=2)
    result = controller.run("Trigger timeout")

    assert result == "Error: Agent reached maximum iterations and failed to answer."
    assert mock_client.chat.call_count == 2