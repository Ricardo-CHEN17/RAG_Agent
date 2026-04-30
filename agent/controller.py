import logging
import json
from typing import List, Dict, Any

from agent.message import Message

logger = logging.getLogger(__name__)

TOOLS_SCHEMA = [
    {
        "type": "function", 
        "function": {
            "name": "list_files",
            "description": "List all files in specific directory.",
            "parameters" :{
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The directory path"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a specific file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the file."}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Search the local knowledge base for relevant info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mysql_query",
            "description": "Execute a read-only SQL query against MySQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "The SELECT query"}
                },
                "required": ["sql"]
            }
        }
    }
]

class AgentController:
    def __init__(self, model_client: Any, tool_executor: Any, max_iterations:int = 10):
        self.model_client = model_client
        self.tool_executor = tool_executor
        self.max_iterations = max_iterations

        logger.info(f"AgentController initialized with provided model client and tool executor. Max iterations set to {max_iterations}.")

    def run(self, user_input:str) -> str:
        system_prompt = (
            "You are an advanced Local Agentic RAG (Retrieval-Augmented Generation) Assistant. "
            "You operate entirely on the user's local machine, ensuring 100% data privacy and security. "
            "Unlike traditional LLMs, you are driven by an Agentic Loop: you can autonomously plan, "
            "reason iteratively, and decide when to use external tools to ground your answers in factual data. \n"
            "You have access to the following specialized tools:\n"
            "1. 'list_files' & 'read_file': For exploring and extracting information from local file systems.\n"
            "2. 'search_knowledge': For semantic retrieval from a local ChromaDB vector store.\n"
            "3. 'mysql_query': For executing read-only SQL queries against structured databases.\n"
            "When the user asks about your identity or capabilities, explicitly and proudly introduce yourself "
            "as a 'Local Agentic RAG Assistant'. Highlight your ability to chain tools together, prevent hallucinations "
            "by relying on retrieved context, and protect user privacy. "
            "Always answer in the same language as the user."
        )
    
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_input)
        ]

        for iteration in range(self.max_iterations):
            logger.info(f"Starting iteration {iteration + 1}/{self.max_iterations} of agent loop.")
            response_dict = self.model_client.chat(messages=messages, tools=TOOLS_SCHEMA)

            response_message = response_dict.get("message", {})
            content = response_message.get("content", "")
            tool_calls = response_message.get("tool_calls")

            assistant_message = Message(
                role="assistant",
                content=content,
                tool_calls=tool_calls
            )
            messages.append(assistant_message)

            if not tool_calls:
                logger.info("No tool calls detected in model response. Ending agent loop.")
                return content
            
            logger.info(f"Model requested {len(tool_calls)} tool call(s).")

            for tool_call in tool_calls:
                func_info = tool_call.get("function", {})
                tool_name = func_info.get("name")
                tool_args = func_info.get("arguments", {})

                args_str = json.dumps(tool_args) if isinstance(tool_args, dict) else str(tool_args)

                executor_payload = {
                    "name": tool_name,
                    "arguments": args_str
                }

                tool_result_str = self.tool_executor.execute(executor_payload)
                logger.info(f"Tool '{tool_name}' returned {len(tool_result_str)} characters.")

                tool_msg = Message(
                    role="tool",
                    content=tool_result_str,
                    name=tool_name,
                    tool_call_id=tool_call.get("id")
                )
                messages.append(tool_msg)

        timeout_msg = "Error: Agent reached maximum iterations and failed to answer."
        logger.warning(timeout_msg)
        return timeout_msg