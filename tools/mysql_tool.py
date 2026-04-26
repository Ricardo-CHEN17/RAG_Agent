"""MySQL tool adapter that formats read-only SQL query results for the agent.

This module bridges the tool executor and the local MySQL client wrapper.
It intentionally exposes a string-based response contract so the agent loop
can forward results directly to the model.
"""

import logging
from db.mysql_client import MySQLClient

logger = logging.getLogger(__name__)

class MySQLTool:
    """Expose read-only SQL query execution through the tool interface."""

    def __init__(self, mysql_client: MySQLClient):
        """Store the injected MySQL client dependency.

        Args:
            mysql_client: Project-local MySQL client used to execute queries.
        """
        self.mysql_client = mysql_client
        logger.info("MySQLTool initialized with provided MySQL client.")

    def query(self, sql: str) -> str:
        """Execute a guarded SELECT query and format the result as a table.

        Args:
            sql: SQL statement submitted by the tool executor.

        Returns:
            str: A markdown-like table string for successful queries, a success
                notice for empty result sets, or an error string beginning with
                ``Error: `` for invalid input or execution failures.
        """
        if not isinstance(sql, str) or sql.strip() == "":
            error_msg = "Invalid SQL query provided."
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        if not sql.strip().upper().startswith("SELECT"):
            error_msg = "Only SELECT queries are allowed."
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        try:
            rows = self.mysql_client.execute_query(sql)
        except Exception as e:
            error_msg = f"Failed to execute SQL query: {str(e)}"
            logger.error(error_msg)
            return f"Error: {error_msg}"
        
        if not rows:
            return "Query executed successfully, but no results were returned."
        
        columns = list(rows[0].keys())
        col_widths = [
            max(len(col), max(len(str(row.get(col, ""))) for row in rows))
            for col in columns
        ]

        header = "| " + " | ".join(
            col.ljust(col_widths[i]) for i, col in enumerate(columns)
        ) + " |"

        separator = "| " + " | ".join("-" * w for w in col_widths) + " |"

        data_rows = "\n".join(
            "| " + " | ".join(
                str(row.get(col, "")).ljust(col_widths[i])
                for i, col in enumerate(columns)
            ) + " |"
            for row in rows
        )

        return "\n".join([header, separator, data_rows])