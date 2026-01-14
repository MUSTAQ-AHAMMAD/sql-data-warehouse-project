"""
Snowflake Database Connector Module

Handles connections and operations with Snowflake data warehouse.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import snowflake.connector
from snowflake.connector import DictCursor
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SnowflakeConnector:
    """
    Connector for Snowflake data warehouse operations.
    """
    
    def __init__(
        self,
        account: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        warehouse: Optional[str] = None,
        database: Optional[str] = None,
        schema: Optional[str] = None,
        role: Optional[str] = None
    ):
        """
        Initialize Snowflake connector.
        
        Args:
            account: Snowflake account identifier
            user: Username
            password: Password
            warehouse: Warehouse name
            database: Database name
            schema: Schema name
            role: Role name
        """
        self.account = account or os.getenv('SNOWFLAKE_ACCOUNT')
        self.user = user or os.getenv('SNOWFLAKE_USER')
        self.password = password or os.getenv('SNOWFLAKE_PASSWORD')
        self.warehouse = warehouse or os.getenv('SNOWFLAKE_WAREHOUSE')
        self.database = database or os.getenv('SNOWFLAKE_DATABASE', 'SALLA_DWH')
        self.schema = schema or os.getenv('SNOWFLAKE_SCHEMA', 'PUBLIC')
        self.role = role or os.getenv('SNOWFLAKE_ROLE')
        
        self.connection = None
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration parameters."""
        required = ['account', 'user', 'password', 'warehouse']
        missing = [param for param in required if not getattr(self, param)]
        
        if missing:
            raise ValueError(f"Missing required Snowflake configuration: {', '.join(missing)}")
    
    def connect(self):
        """Establish connection to Snowflake."""
        try:
            logger.info(f"Connecting to Snowflake account: {self.account}")
            
            self.connection = snowflake.connector.connect(
                account=self.account,
                user=self.user,
                password=self.password,
                warehouse=self.warehouse,
                database=self.database,
                schema=self.schema,
                role=self.role
            )
            
            logger.info("Successfully connected to Snowflake")
            return self.connection
            
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            raise
    
    def close(self):
        """Close Snowflake connection."""
        if self.connection:
            self.connection.close()
            logger.info("Snowflake connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries containing query results
        """
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor(DictCursor)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
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
            
            # Split and execute each statement
            statements = [s.strip() for s in script.split(';') if s.strip()]
            
            for statement in statements:
                logger.info(f"Executing: {statement[:100]}...")
                cursor.execute(statement)
            
            cursor.close()
            logger.info("Script executed successfully")
            
        except Exception as e:
            logger.error(f"Script execution failed: {str(e)}")
            raise
    
    def load_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = 'append'
    ):
        """
        Load pandas DataFrame into Snowflake table.
        
        Args:
            df: Pandas DataFrame to load
            table_name: Target table name
            if_exists: How to behave if table exists ('append', 'replace', 'fail')
        """
        if not self.connection:
            self.connect()
        
        try:
            logger.info(f"Loading {len(df)} records into {table_name}")
            
            # Use pandas to_sql with Snowflake connector
            from snowflake.connector.pandas_tools import write_pandas
            
            success, nchunks, nrows, _ = write_pandas(
                self.connection,
                df,
                table_name,
                auto_create_table=False,
                overwrite=(if_exists == 'replace')
            )
            
            if success:
                logger.info(f"Successfully loaded {nrows} rows into {table_name}")
            else:
                logger.error(f"Failed to load data into {table_name}")
            
        except Exception as e:
            logger.error(f"DataFrame load failed: {str(e)}")
            raise
    
    def bulk_insert(
        self,
        table_name: str,
        records: List[Dict],
        batch_size: int = 1000
    ):
        """
        Insert records in bulk with batching.
        
        Args:
            table_name: Target table name
            records: List of dictionaries containing record data
            batch_size: Number of records per batch
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
                self.load_dataframe(batch, table_name, if_exists='append')
            
            logger.info(f"Successfully inserted {len(records)} records into {table_name}")
            
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
        with SnowflakeConnector() as sf:
            result = sf.execute_query("SELECT CURRENT_VERSION()")
            print(f"Snowflake version: {result}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
