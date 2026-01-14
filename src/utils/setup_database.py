"""
Database Schema Setup Script

This script creates all database schemas and tables for Bronze, Silver, and Gold layers.
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.snowflake_connector import SnowflakeConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_schemas():
    """Create all schemas and tables in Snowflake."""
    
    # Get SQL file paths
    sql_dir = Path(__file__).parent.parent / 'sql'
    bronze_sql = sql_dir / 'bronze' / 'create_bronze_tables.sql'
    silver_sql = sql_dir / 'silver' / 'create_silver_tables.sql'
    gold_sql = sql_dir / 'gold' / 'create_gold_tables.sql'
    
    try:
        with SnowflakeConnector() as sf:
            logger.info("Creating Bronze layer tables...")
            with open(bronze_sql, 'r') as f:
                sf.execute_script(f.read())
            logger.info("Bronze layer created successfully")
            
            logger.info("Creating Silver layer tables...")
            with open(silver_sql, 'r') as f:
                sf.execute_script(f.read())
            logger.info("Silver layer created successfully")
            
            logger.info("Creating Gold layer tables...")
            with open(gold_sql, 'r') as f:
                sf.execute_script(f.read())
            logger.info("Gold layer created successfully")
            
            logger.info("All schemas and tables created successfully!")
            
    except Exception as e:
        logger.error(f"Schema setup failed: {str(e)}")
        raise


if __name__ == "__main__":
    setup_schemas()
