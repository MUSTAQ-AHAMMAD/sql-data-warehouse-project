"""
Database Schema Setup Script
Creates all database schemas and tables for Bronze, Silver, and Gold layers.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_schemas():
    """Create all schemas and tables in the database."""
    
    # Get database type from environment
    db_type = os.getenv('DATABASE_TYPE', 'snowflake').lower()
    
    # Get SQL file paths
    sql_dir = project_root / 'sql'
    bronze_sql = sql_dir / 'bronze' / 'create_bronze_tables.sql'
    silver_sql = sql_dir / 'silver' / 'create_silver_tables.sql'
    gold_sql = sql_dir / 'gold' / 'create_gold_tables.sql'
    
    try:
        if db_type == 'sqlserver':
            from src.database.sqlserver_connector import SQLServerConnector
            
            logger.info("Using SQL Server database")
            with SQLServerConnector() as db:
                logger.info("Creating Bronze layer tables...")
                with open(bronze_sql, 'r') as f:
                    db.execute_script(f.read())
                logger.info("✅ Bronze layer created successfully")
                
                logger.info("Creating Silver layer tables...")
                with open(silver_sql, 'r') as f:
                    db.execute_script(f.read())
                logger.info("✅ Silver layer created successfully")
                
                logger.info("Creating Gold layer tables...")
                with open(gold_sql, 'r') as f:
                    db.execute_script(f.read())
                logger.info("✅ Gold layer created successfully")
                
        elif db_type == 'snowflake':
            from src.database.snowflake_connector import SnowflakeConnector
            
            logger.info("Using Snowflake database")
            with SnowflakeConnector() as db:
                logger.info("Creating Bronze layer tables...")
                with open(bronze_sql, 'r') as f:
                    db.execute_script(f.read())
                logger.info("✅ Bronze layer created successfully")
                
                logger.info("Creating Silver layer tables...")
                with open(silver_sql, 'r') as f:
                    db.execute_script(f.read())
                logger.info("✅ Silver layer created successfully")
                
                logger.info("Creating Gold layer tables...")
                with open(gold_sql, 'r') as f:
                    db.execute_script(f.read())
                logger.info("✅ Gold layer created successfully")
        
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        logger.info("\n🎉 All schemas and tables created successfully!")
        logger.info(f"Database: {db_type.upper()}")
        
    except FileNotFoundError as e:
        logger.error(f"SQL file not found: {e}")
        logger.error(f"Make sure SQL files exist in: {sql_dir}")
        raise
    except Exception as e:
        logger.error(f"Schema setup failed: {str(e)}")
        raise


if __name__ == "__main__":
    setup_schemas()
