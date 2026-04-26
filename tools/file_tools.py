"""File-system tool helpers used by the agent tool executor.

The methods in this module intentionally return human-readable strings so the
tool executor and LLM loop can consume outputs directly.
"""

import os
import logging

logger = logging.getLogger(__name__)

class FileTools:
    """Expose safe, read-only file operations for tool calls."""

    def __init__(self):
        """Initialize a FileTools instance."""
        pass

    def list_files(self, path: str) -> str:
        """List directory entries and return a formatted newline-separated string.

        Args:
            path: Directory path to inspect.

        Returns:
            str: Formatted listing output, or an error string starting with
                "Error: " when validation or OS operations fail.
        """
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

        result = f"files in {path}:\n" + "\n".join(sorted(entries))
        logger.info(f"Listed {len(entries)} entries in directory: {path}")
        return result

    def read_file(self, file_path: str, max_chars: int = 10000) -> str:
        """Read UTF-8 text content with optional truncation.

        Args:
            file_path: Text file path to read.
            max_chars: Maximum number of characters returned before truncation.

        Returns:
            str: File content, possibly truncated with a suffix note, or an
                error string starting with "Error: " for invalid inputs or IO
                failures.
        """
        if not file_path or not isinstance(file_path, str):
            return f"Error: Invalid file path provided."
        if not isinstance(max_chars, int) or max_chars <= 0:
            return f"Error: Invalid max_chars provided."
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        if not os.path.isfile(file_path):
            return f"Error: Not a file: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read only enough to decide truncation, then stream-count the rest.
                preview = f.read(max_chars + 1)
                is_truncated = len(preview) > max_chars

                if is_truncated:
                    content = preview[:max_chars]
                    origin_length = len(preview)
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        origin_length += len(chunk)
                else:
                    content = preview
                    origin_length = len(content)

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
        
        if is_truncated:
            logger.warning(f"File content exceeds max character limit ({max_chars}). Truncating output.")
            content = content + f"\n\n[...Truncated at {max_chars} chars, original size: {origin_length} chars]"
        
        logger.info(f"Read file: {file_path} (length: {len(content)} chars)")
        return content