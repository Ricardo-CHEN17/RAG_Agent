import os
import logging
from typing import Any, Dict, Optional, List

import mysql.connector
from mysql.connector import Error as MySQLError

logger = logging.getLogger(__name__)

def get_db_client_from_env() -> "MySQLClient":
    host = os.getenv("MYSQL_HOST")
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")

    missing_vars = [var for var in ["MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE"] if not os.getenv(var)]
    if missing_vars:
        error_msg = f"Missing required environment variables for MySQLClient: {', '.join(missing_vars)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        client = MySQLClient(host=host, user=user, password=password, database=database)
        logger.info("Successfully created MySQLClient from environment variables.")
        return client
    except Exception as e:
        error_msg = f"Failed to create MySQLClient from environment variables: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(f"Failed to create MySQLClient: {e}") from e

    
class MySQLClient:
    def __init__(self, host: str, user: str, password: str, database: str):
        missing = [var for var in [host, user, database] if not var]
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
        if not isinstance(sql, str) or sql.strip() == "":
            logger.error("SQL query must be a non-empty string.")
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
        if not isinstance(sql, str) or sql.strip() == "":
            logger.error("SQL update statement must be a non-empty string.")
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