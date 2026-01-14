"""
SQL Server Database Connector Module

Handles connections and operations with SQL Server data warehouse (on-premise or cloud).
This is an alternative to Snowflake for organizations requiring on-premise solutions.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import pyodbc
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLServerConnector:
    """
    Connector for SQL Server data warehouse operations.
    Supports both on-premise SQL Server and Azure SQL Database.
    """
    
    def __init__(
        self,
        server: Optional[str] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        driver: Optional[str] = None,
        port: Optional[int] = None,
        trusted_connection: Optional[bool] = None
    ):
        """
        Initialize SQL Server connector.
        
        Args:
            server: SQL Server hostname or IP (e.g., 'localhost', '192.168.1.100')
            database: Database name
            username: Username for SQL authentication
            password: Password for SQL authentication
            driver: ODBC driver (defaults to 'ODBC Driver 17 for SQL Server')
            port: SQL Server port (defaults to 1433)
            trusted_connection: Use Windows Authentication (defaults to False)
        """
        self.server = server or os.getenv('SQLSERVER_HOST', 'localhost')
        self.database = database or os.getenv('SQLSERVER_DATABASE', 'SALLA_DWH')
        self.username = username or os.getenv('SQLSERVER_USER')
        self.password = password or os.getenv('SQLSERVER_PASSWORD')
        self.driver = driver or os.getenv('SQLSERVER_DRIVER', 'ODBC Driver 17 for SQL Server')
        self.port = port or int(os.getenv('SQLSERVER_PORT', '1433'))
        self.trusted_connection = trusted_connection or os.getenv('SQLSERVER_TRUSTED_CONNECTION', 'False').lower() == 'true'
        
        self.connection = None
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration parameters."""
        if not self.server:
            raise ValueError("SQL Server host is required. Set SQLSERVER_HOST environment variable.")
        
        if not self.trusted_connection and (not self.username or not self.password):
            raise ValueError("Username and password required for SQL authentication, or enable trusted connection.")
    
    def connect(self):
        """Establish connection to SQL Server."""
        try:
            logger.info(f"Connecting to SQL Server: {self.server}")
            
            # Build connection string
            if self.trusted_connection:
                # Windows Authentication
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server},{self.port};"
                    f"DATABASE={self.database};"
                    f"Trusted_Connection=yes;"
                )
            else:
                # SQL Server Authentication
                connection_string = (
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server},{self.port};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                )
            
            self.connection = pyodbc.connect(connection_string, timeout=30)
            logger.info("Successfully connected to SQL Server")
            return self.connection
            
        except Exception as e:
            logger.error(f"Failed to connect to SQL Server: {str(e)}")
            raise
    
    def close(self):
        """Close SQL Server connection."""
        if self.connection:
            self.connection.close()
            logger.info("SQL Server connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        Execute a SQL query and return results as list of dictionaries.
        
        Args:
            query: SQL query string
            params: Query parameters for parameterized queries
            
        Returns:
            List of dictionaries containing query results
        """
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [column[0] for column in cursor.description] if cursor.description else []
            
            # Fetch all rows
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            results = [dict(zip(columns, row)) for row in rows]
            
            cursor.close()
            return results
            
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def execute_script(self, script: str):
        """
        Execute a SQL script (multiple statements).
        
        Args:
            script: SQL script containing multiple statements
        """
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            # SQL Server doesn't support multiple statements in one execute
            # Split by GO statement (SQL Server batch separator)
            batches = [batch.strip() for batch in script.split('GO') if batch.strip()]
            
            for batch in batches:
                # Further split by semicolon for individual statements
                statements = [s.strip() for s in batch.split(';') if s.strip()]
                
                for statement in statements:
                    logger.info(f"Executing: {statement[:100]}...")
                    cursor.execute(statement)
            
            self.connection.commit()
            cursor.close()
            logger.info("Script executed successfully")
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Script execution failed: {str(e)}")
            raise
    
    def load_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = 'append',
        schema: str = 'dbo'
    ):
        """
        Load pandas DataFrame into SQL Server table.
        
        Args:
            df: Pandas DataFrame to load
            table_name: Target table name
            if_exists: How to behave if table exists ('append', 'replace', 'fail')
            schema: Schema name (defaults to 'dbo')
        """
        if not self.connection:
            self.connect()
        
        try:
            logger.info(f"Loading {len(df)} records into {schema}.{table_name}")
            
            # Check if table exists
            cursor = self.connection.cursor()
            check_query = f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            """
            cursor.execute(check_query, (schema, table_name))
            table_exists = cursor.fetchone()[0] > 0
            cursor.close()
            
            if not table_exists and if_exists == 'append':
                logger.warning(f"Table {schema}.{table_name} does not exist. It must be created first.")
                raise ValueError(f"Table {schema}.{table_name} does not exist")
            
            # Use pandas to_sql with pyodbc
            # Note: This requires SQLAlchemy for better performance
            from sqlalchemy import create_engine
            from urllib.parse import quote_plus
            
            if self.trusted_connection:
                connection_url = f"mssql+pyodbc://@{self.server}:{self.port}/{self.database}?driver={self.driver.replace(' ', '+')}&trusted_connection=yes"
            else:
                params = quote_plus(
                    f"DRIVER={{{self.driver}}};"
                    f"SERVER={self.server},{self.port};"
                    f"DATABASE={self.database};"
                    f"UID={self.username};"
                    f"PWD={self.password};"
                )
                connection_url = f"mssql+pyodbc:///?odbc_connect={params}"
            
            engine = create_engine(connection_url)
            
            df.to_sql(
                name=table_name,
                con=engine,
                schema=schema,
                if_exists=if_exists,
                index=False,
                method='multi',  # Bulk insert for better performance
                chunksize=1000
            )
            
            logger.info(f"Successfully loaded {len(df)} rows into {schema}.{table_name}")
            
        except Exception as e:
            logger.error(f"DataFrame load failed: {str(e)}")
            raise
    
    def bulk_insert(
        self,
        table_name: str,
        records: List[Dict],
        batch_size: int = 1000,
        schema: str = 'dbo'
    ):
        """
        Insert records in bulk with batching for better performance.
        
        Args:
            table_name: Target table name
            records: List of dictionaries containing record data
            batch_size: Number of records per batch
            schema: Schema name (defaults to 'dbo')
        """
        if not records:
            logger.warning("No records to insert")
            return
        
        if not self.connection:
            self.connect()
        
        try:
            # Convert to DataFrame for easier handling
            df = pd.DataFrame(records)
            
            # Insert in batches
            total_batches = (len(df) - 1) // batch_size + 1
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                batch_num = i // batch_size + 1
                
                logger.info(f"Inserting batch {batch_num}/{total_batches}")
                self.load_dataframe(batch, table_name, if_exists='append', schema=schema)
            
            logger.info(f"Successfully inserted {len(records)} records into {schema}.{table_name}")
            
        except Exception as e:
            logger.error(f"Bulk insert failed: {str(e)}")
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    # Example usage
    try:
        # Test connection with Windows Authentication
        with SQLServerConnector() as sql:
            result = sql.execute_query("SELECT @@VERSION as version")
            print(f"SQL Server version: {result[0]['version']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
