"""MySQL client utilities for environment-based initialization and basic CRUD execution.

This module provides a thin wrapper around ``mysql.connector`` for local project use.
It keeps execution APIs simple and returns sentinel values on runtime query/update
failures to match the current tool-executor integration contract.
"""

import os
import logging
from typing import Dict, List

import mysql.connector
from mysql.connector import Error as MySQLError

logger = logging.getLogger(__name__)


def get_db_client_from_env() -> "MySQLClient":
    """Create a ``MySQLClient`` from required environment variables.

    Required variables:
    - ``MYSQL_HOST``
    - ``MYSQL_USER``
    - ``MYSQL_PASSWORD``
    - ``MYSQL_DATABASE``

    Returns:
        MySQLClient: An initialized and connected database client.

    Raises:
        RuntimeError: If required environment variables are missing or client
            initialization fails.
    """
    env_values = {
        "MYSQL_HOST": os.getenv("MYSQL_HOST"),
        "MYSQL_USER": os.getenv("MYSQL_USER"),
        "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
        "MYSQL_DATABASE": os.getenv("MYSQL_DATABASE"),
    }
    missing_vars = [name for name, value in env_values.items() if not value]
    if missing_vars:
        error_msg = f"Missing required environment variables for MySQLClient: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        client = MySQLClient(
            host=env_values["MYSQL_HOST"],
            user=env_values["MYSQL_USER"],
            password=env_values["MYSQL_PASSWORD"],
            database=env_values["MYSQL_DATABASE"],
        )
        logger.info("Successfully created MySQLClient from environment variables.")
        return client
    except (ValueError, RuntimeError) as e:
        error_msg = f"Failed to create MySQLClient from environment variables: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(f"Failed to create MySQLClient: {e}") from e

    
class MySQLClient:
    """Lightweight MySQL connector wrapper for query and update operations."""

    def __init__(self, host: str, user: str, password: str, database: str):
        """Initialize and open a MySQL connection.

        Args:
            host: MySQL server host.
            user: MySQL username.
            password: MySQL password.
            database: Default database name.

        Raises:
            ValueError: If any required argument is empty.
            RuntimeError: If database connection fails.
        """
        values = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ValueError(f"Missing required arguments for MySQLClient: {', '.join(missing)}")

        self.host = host
        self.user = user
        self.password = password
        self.database = database

        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                logger.info(f"Connected to MySQL database '{self.database}' at '{self.host}' as user '{self.user}'.")
        except MySQLError as e:
            error_msg = f"Error connecting to MySQL database: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def execute_query(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute a read query and return rows as a list of dictionaries.

        Args:
            sql: SQL statement to execute.
            params: Positional parameters for the SQL statement.

        Returns:
            List[Dict]: Query result rows. Returns an empty list for invalid SQL,
                unavailable connection, or query execution errors.
        """
        if not isinstance(sql, str) or sql.strip() == "":
            logger.error("SQL query must be a non-empty string.")
            return []

        if not self.connection or not self.connection.is_connected():
            logger.error("MySQL connection is not available.")
            return []

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchall()

            logger.debug(f"Executed query: {sql} with params: {params}. Result count: {len(result)}")

            return result

        except MySQLError as e:
            error_msg = f"Error executing query: {str(e)}"
            logger.error(error_msg)
            return []
        
    def execute_update(self, sql: str, params: tuple = ()) -> int:
        """Execute a write statement and return affected row count.

        Args:
            sql: SQL update/insert/delete statement.
            params: Positional parameters for the SQL statement.

        Returns:
            int: Number of affected rows. Returns ``0`` for invalid SQL,
                unavailable connection, or execution errors.
        """
        if not isinstance(sql, str) or sql.strip() == "":
            logger.error("SQL update statement must be a non-empty string.")
            return 0

        if not self.connection or not self.connection.is_connected():
            logger.error("MySQL connection is not available.")
            return 0
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                self.connection.commit()
                affected_rows = cursor.rowcount

            logger.debug(f"Executed update: {sql} with params: {params}. Affected rows: {affected_rows}")

            return affected_rows
        
        except MySQLError as e:
            error_msg = f"Error executing update: {str(e)}"
            logger.error(error_msg)
            return 0
        
    def close(self) -> None:
        """Close the active MySQL connection if it is currently open."""
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
                logger.info("MySQL connection closed.")
            except MySQLError as e:
                logger.error(f"Error closing MySQL connection: {str(e)}")