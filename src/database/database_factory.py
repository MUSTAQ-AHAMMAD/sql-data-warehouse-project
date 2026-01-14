"""
Database Connector Factory

Factory pattern to support multiple database backends (Snowflake, SQL Server, etc.)
Allows easy switching between cloud and on-premise databases.
"""

import os
import logging
from typing import Union
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_connector() -> Union['SnowflakeConnector', 'SQLServerConnector']:
    """
    Factory method to get the appropriate database connector based on configuration.
    
    Returns:
        Database connector instance (SnowflakeConnector or SQLServerConnector)
        
    Raises:
        ValueError: If database type is not supported
        
    Environment Variables:
        DATABASE_TYPE: Type of database to use ('snowflake' or 'sqlserver')
    """
    db_type = os.getenv('DATABASE_TYPE', 'snowflake').lower()
    
    logger.info(f"Initializing database connector: {db_type}")
    
    if db_type == 'snowflake':
        from src.database.snowflake_connector import SnowflakeConnector
        return SnowflakeConnector()
    
    elif db_type == 'sqlserver':
        from src.database.sqlserver_connector import SQLServerConnector
        return SQLServerConnector()
    
    else:
        raise ValueError(
            f"Unsupported database type: {db_type}. "
            f"Supported types: 'snowflake', 'sqlserver'"
        )


def get_database_type() -> str:
    """
    Get the configured database type.
    
    Returns:
        Database type string ('snowflake' or 'sqlserver')
    """
    return os.getenv('DATABASE_TYPE', 'snowflake').lower()


def is_snowflake() -> bool:
    """Check if using Snowflake database."""
    return get_database_type() == 'snowflake'


def is_sqlserver() -> bool:
    """Check if using SQL Server database."""
    return get_database_type() == 'sqlserver'


if __name__ == "__main__":
    # Test factory
    try:
        db = get_database_connector()
        print(f"✓ Successfully initialized {type(db).__name__}")
        
        with db as conn:
            # Test connection
            if is_snowflake():
                result = conn.execute_query("SELECT CURRENT_VERSION()")
                print(f"✓ Snowflake version: {result}")
            elif is_sqlserver():
                result = conn.execute_query("SELECT @@VERSION as version")
                print(f"✓ SQL Server version: {result[0]['version'][:50]}...")
                
    except Exception as e:
        print(f"✗ Error: {str(e)}")
