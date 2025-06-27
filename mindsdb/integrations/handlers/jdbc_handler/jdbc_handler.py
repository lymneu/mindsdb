# 文件名: jdbc_handler.py
import os
from typing import Text, Dict, Optional

import pandas as pd
import jaydebeapi
from jaydebeapi import Error as JayDeBeAPIError

from mindsdb.integrations.libs.base import DatabaseHandler
from mindsdb.integrations.libs.response import (
    HandlerStatusResponse as StatusResponse,
    HandlerResponse as Response,
    RESPONSE_TYPE
)
from mindsdb.utilities import log
from mindsdb_sql_parser.ast.base import ASTNode

logger = log.getLogger(__name__)


class JDBCHandler(DatabaseHandler):
    """
    This handler handles connection and execution of SQL statements on any database with a JDBC driver.
    """
    name = 'jdbc'

    def __init__(self, name: Text, connection_data: Optional[Dict], **kwargs) -> None:
        super().__init__(name)
        self.connection_data = connection_data
        self.kwargs = kwargs
        self.connection = None
        self.is_connected = False

    def __del__(self) -> None:
        if self.is_connected:
            self.disconnect()

    def connect(self):
        if self.is_connected:
            return self.connection

        required_params = ['driver_class_name', 'connection_string', 'user', 'jdbc_driver_path']
        if not all(key in self.connection_data for key in required_params):
            raise ValueError(f"Required parameters for JDBC handler are missing. Need: {required_params}")

        driver_class = self.connection_data['driver_class_name']
        url = self.connection_data['connection_string']
        user = self.connection_data['user']
        password = self.connection_data.get('password')
        driver_path = self.connection_data['jdbc_driver_path']

        if not os.path.exists(driver_path):
            raise ValueError(f"Provided jdbc_driver_path does not exist: {driver_path}")

        jars = []
        if os.path.isdir(driver_path):
            jars = [os.path.join(driver_path, f) for f in os.listdir(driver_path) if f.lower().endswith('.jar')]
            if not jars:
                raise ValueError(f"No .jar files found in the specified directory: {driver_path}")
        elif os.path.isfile(driver_path):
            jars = [driver_path]

        logger.info(f"Found {len(jars)} JAR files to load from {driver_path}")

        conn_args = [user]
        if password:
            conn_args.append(password)

        try:
            logger.info(f"Attempting to connect via JDBC with driver {driver_class}...")
            self.connection = jaydebeapi.connect(driver_class, url, conn_args, jars=jars)
            self.is_connected = True
            logger.info("JDBC Connection Successful.")
            return self.connection
        except JayDeBeAPIError as e:
            logger.error(f"Error connecting via JDBC: {e}")
            raise
        except Exception as e:
            logger.error(f"An unknown error occurred during JDBC connection: {e}")
            raise

    def disconnect(self) -> None:
        if self.is_connected:
            self.connection.close()
            self.is_connected = False

    def check_connection(self) -> StatusResponse:
        response = StatusResponse(False)
        try:
            self.connect()
            response.success = True
        except Exception as e:
            logger.error(f'Connection check to JDBC failed: {e}')
            response.error_message = str(e)

        if self.is_connected:
            self.disconnect()
        return response

    def native_query(self, query: str) -> Response:
        need_to_close = not self.is_connected
        conn = self.connect()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                if result:
                    response = Response(
                        RESPONSE_TYPE.TABLE,
                        data_frame=pd.DataFrame(result, columns=[desc[0] for desc in cursor.description])
                    )
                else:
                    response = Response(RESPONSE_TYPE.OK)
        except Exception as e:
            logger.error(f"Error running query '{query}' via JDBC!")
            response = Response(RESPONSE_TYPE.ERROR, error_message=str(e))

        if need_to_close:
            self.disconnect()
        return response

    def query(self, query: ASTNode) -> Response:
        return self.native_query(query.to_string())

    def get_tables(self) -> Response:
        """
        Retrieves a list of all non-system tables.
        """
        # Run the query to get a list of tables
        result = self.native_query("SHOW TABLES")

        # The result from Hive's "SHOW TABLES" has a column often named 'tab_name'.
        # The MindsDB API expects this column to be named 'table_name'.
        # We must rename it to ensure compatibility with the GUI.
        if result.type == RESPONSE_TYPE.TABLE and not result.data_frame.empty:
            # Get the original column name (it's the first and only one)
            original_col_name = result.data_frame.columns[0]
            # Rename it to what the API expects
            result.data_frame = result.data_frame.rename(columns={original_col_name: 'table_name'})

        return result

    def get_columns(self, table_name: str) -> Response:
        return self.native_query(f"DESCRIBE {table_name}")