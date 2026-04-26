"""Message and tool-call data models used in agent/model interactions."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """Structured representation of a single tool call payload."""

    id: str
    type: str
    function_name: str
    arguments: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the tool call into OpenAI/Ollama-compatible dict format.

        Returns:
            Dict[str, Any]: Tool-call payload following common chat API schema.
        """
        return {
            "id": self.id,
            "type": self.type,
            "function": {
                "name": self.function_name,
                "arguments": self.arguments,
            },
        }


@dataclass
class Message:
    """Canonical chat message object exchanged with model APIs."""

    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the message while omitting optional fields when absent.

        Returns:
            Dict[str, Any]: Message dictionary compatible with chat API input.
        """
        data: Dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.tool_calls is not None:
            data["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            data["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            data["name"] = self.name
        return data
