import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class ToolExecutor:
    def __init__(self, file_tools: Any, rag_tool: Any, mysql_tool: Any = None):
        self.file_tools = file_tools
        self.rag_tool = rag_tool
        self.mysql_tool = mysql_tool

        logger.info("ToolExecutor initialized with provided tool dependencies.")

    def _list_files(self, path: str) -> str:
        return self.file_tools.list_files(path)
    
    def _read_file(self, file_path: str, max_chars: int = 10000) -> str:
        return self.file_tools.read_file(file_path, max_chars)
    
    def _search_knowledge(self, query: str, top_k: int = 3) -> str:
        return self.rag_tool.search_knowledge(query, top_k)
    
    def _mysql_query(self, sql: str) -> str:
        if not self.mysql_tool:
            return "Error: MySQL tool is not available."
        return self.mysql_tool.query(sql)
    
    def execute(self, tool_call: Dict[str, Any]) -> str:
        try:
            name = tool_call.get('name')
            arguments_str = tool_call.get('arguments', '{}')

            arguments = json.loads(arguments_str) if arguments_str else {}
            logger.info(f"Executing tool call: {name} with arguments: {arguments}")

            if name == 'list_files':
                result = self._list_files(path=arguments.get("path", "."))

            elif name == "read_file":
                file_path = arguments.get("file_path")
                if not file_path:
                    return "Error: Missing required argument 'file_path'."
                result = self._read_file(file_path=file_path)
            
            elif name == "search_knowledge":
                query = arguments.get("query")
                if not query:
                    return "Error: Query text is required."
                result = self._search_knowledge(query=query)
            
            elif name == "mysql_query":
                sql = arguments.get("sql")
                if not sql:
                    return "Error: SQL query text is required."
                result = self._mysql_query(sql=sql)
            
            else:
                result = f"Error: Unknown tool name: {name}"
                logger.error(result)

            return str(result)

        except json.JSONDecodeError as e:
            error_msg = f"Error: Failed to parse arguments as JSON: {str(e)}"
            logger.error(error_msg)
            return error_msg

        except Exception as e:
            error_msg = f"Failed to execute tool call: {tool_call.get('name', 'unknown')} with error: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"