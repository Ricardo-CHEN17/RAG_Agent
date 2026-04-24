import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

class FileTools:
    def __init__(self):
        pass

    def list_files(self, path: str) -> str:
        if not path or not isinstance(path, str):
            return f"Error: Invalid path provided."
        if not os.path.exists(path):
            return f"Error: Directory not found: {path}"
        if not os.path.isdir(path):
            return f"Error: Not a directory: {path}"
        
        try:
            entries = os.listdir(path)
        except PermissionError:
            logger.error(f"Permission denied for directory: {path}")
            return f"Error: Permission denied for directory: {path}"
        except OSError as e:
            logger.error(f"Error occurred while listing directory contents: {e}")
            return f"Error: {e}"
        
        if not entries:
            return f"Directory is empty: {path}"
        
        entries.sort()
        result = f"files in {path}:\n" + "\n".join(entries)
        logger.info(f"Listed {len(entries)} entries in directory: {path}")
        return result

    def read_file(self, file_path: str, max_chars: int = 10000) -> str:
        if not file_path or not isinstance(file_path, str):
            return f"Error: Invalid file path provided."
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        if not os.path.isfile(file_path):
            return f"Error: Not a file: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return f"Error: File not found: {file_path}"
        except PermissionError:
            logger.error(f"Permission denied for file: {file_path}")
            return f"Error: Permission denied for file: {file_path}"
        except UnicodeDecodeError:
            logger.error(f"Error: Unable to decode file (try a different encoding): {file_path}")
            return f"Error: Unable to decode file (try a different encoding): {file_path}"
        except OSError as e:
            logger.error(f"Error occurred while reading file: {e}")
            return f"Error: {e}"
        
        if len(content) > max_chars:
            origin_length = len(content)
            logger.warning(f"File content exceeds max character limit ({max_chars}). Truncating output.")
            content = content[:max_chars] + f"\n\n[...Truncated at {max_chars} chars, original size: {origin_length} chars]"
        
        logger.info(f"Read file: {file_path} (length: {len(content)} chars)")
        return content