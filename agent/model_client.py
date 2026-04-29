import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional

from agent.message import Message

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, model_name: str = None, base_url: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL_NAME", "gemma4")

        logger.info(f"OllamaClient initialized with model: {self.model_name} at base URL: {self.base_url}")

    def chat(self, messages: List[Message], tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/chat"
        formatted_messages = [msg.to_dict() for msg in messages]

        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "stream": False
        }

        if tools:
            payload["tools"] = tools
        
        logger.info(f"Sending chat request. Model: {self.model_name}, Messages count: {len(messages)}, Tools available: {bool(tools)}")

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            logger.info("Received response from Ollama successfully.")

            return response.json()
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to communicate with Ollama API: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e