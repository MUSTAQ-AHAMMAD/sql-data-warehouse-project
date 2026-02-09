"""
Incremental Load Manager

Manages watermark tracking and incremental data loading to prevent duplicates.
Works with any database backend via factory pattern.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from dotenv import load_dotenv

from src.database.database_factory import get_database_connector

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IncrementalManager:
    """
    Manages incremental loading with watermark tracking.
    
    Prevents duplicate data loads by tracking the last successful load timestamp
    for each entity type.
    """
    
    def __init__(self):
        """Initialize the incremental manager with database connection."""
        self.db = get_database_connector()
        self._ensure_watermark_table()
    
    def _ensure_watermark_table(self):
        """Create watermark tracking table if it doesn't exist."""
        try:
            with self.db as conn:
                # Check if table exists
                check_query = """
                    SELECT COUNT(*) as cnt 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_SCHEMA = 'BRONZE' 
                    AND TABLE_NAME = 'load_watermarks'
                """
                
                result = conn.execute_query(check_query)
                
                if result[0]['cnt'] == 0:
                    # Create watermark table
                    create_query = """
                        CREATE TABLE BRONZE.load_watermarks (
                            entity_name VARCHAR(100) PRIMARY KEY,
                            last_load_timestamp DATETIME NOT NULL,
                            records_loaded INT DEFAULT 0,
                            load_duration_seconds FLOAT DEFAULT 0,
                            load_rate_records_per_sec FLOAT DEFAULT 0,
                            created_at DATETIME DEFAULT GETDATE(),
                            updated_at DATETIME DEFAULT GETDATE()
                        )
                    """
                    conn.execute_query(create_query)
                    logger.info("✅ Created watermark tracking table")
                    
        except Exception as e:
            logger.warning(f"Could not create watermark table: {str(e)}")
    
    def get_last_load_timestamp(self, entity_name: str) -> Optional[datetime]:
        """
        Get the last successful load timestamp for an entity.
        
        Args:
            entity_name: Name of the entity (e.g., 'orders', 'customers', 'products')
            
        Returns:
            Last load timestamp or None if never loaded
        """
        try:
            with self.db as conn:
                query = """
                    SELECT last_load_timestamp 
                    FROM BRONZE.load_watermarks 
                    WHERE entity_name = ?
                """
                
                result = conn.execute_query(query, (entity_name,))
                
                if result and len(result) > 0:
                    timestamp = result[0]['last_load_timestamp']
                    logger.info(f"Last load for {entity_name}: {timestamp}")
                    return timestamp
                else:
                    logger.info(f"No previous load found for {entity_name}")
                    return None
                    
        except Exception as e:
            logger.warning(f"Error getting watermark for {entity_name}: {str(e)}")
            return None
    
    def update_watermark(self, entity_name: str, timestamp: datetime, 
                        records_loaded: int = 0, duration_seconds: float = 0):
        """
        Update the watermark for an entity after successful load.
        
        Args:
            entity_name: Name of the entity
            timestamp: Timestamp of the successful load
            records_loaded: Number of records loaded
            duration_seconds: Time taken for the load
        """
        try:
            rate = records_loaded / duration_seconds if duration_seconds > 0 else 0
            
            with self.db as conn:
                # Try to update existing record
                update_query = """
                    UPDATE BRONZE.load_watermarks 
                    SET last_load_timestamp = ?,
                        records_loaded = ?,
                        load_duration_seconds = ?,
                        load_rate_records_per_sec = ?,
                        updated_at = GETDATE()
                    WHERE entity_name = ?
                """
                
                conn.execute_query(update_query, 
                                 (timestamp, records_loaded, duration_seconds, rate, entity_name))
                
                # If no rows were updated, insert new record
                check_query = """
                    SELECT COUNT(*) as cnt 
                    FROM BRONZE.load_watermarks 
                    WHERE entity_name = ?
                """
                result = conn.execute_query(check_query, (entity_name,))
                
                if result[0]['cnt'] == 0:
                    insert_query = """
                        INSERT INTO BRONZE.load_watermarks 
                        (entity_name, last_load_timestamp, records_loaded, 
                         load_duration_seconds, load_rate_records_per_sec)
                        VALUES (?, ?, ?, ?, ?)
                    """
                    conn.execute_query(insert_query, 
                                     (entity_name, timestamp, records_loaded, 
                                      duration_seconds, rate))
                
                logger.info(f"✅ Updated watermark for {entity_name}: "
                          f"{records_loaded} records in {duration_seconds:.2f}s "
                          f"({rate:.2f} rec/sec)")
                
        except Exception as e:
            logger.error(f"Error updating watermark for {entity_name}: {str(e)}")
            raise
    
    def get_incremental_date_range(self, entity_name: str, 
                                   default_lookback_days: int = 30) -> Dict[str, datetime]:
        """
        Calculate the date range for incremental load.
        
        Args:
            entity_name: Name of the entity
            default_lookback_days: Days to look back if no previous load
            
        Returns:
            Dictionary with 'start_date' and 'end_date'
        """
        last_load = self.get_last_load_timestamp(entity_name)
        end_date = datetime.now()
        
        if last_load:
            # Add small overlap to catch any late-arriving data
            start_date = last_load - timedelta(hours=1)
        else:
            # First load - go back default days
            start_date = end_date - timedelta(days=default_lookback_days)
        
        logger.info(f"Incremental load range for {entity_name}: "
                   f"{start_date} to {end_date}")
        
        return {
            'start_date': start_date,
            'end_date': end_date
        }
    
    def log_load_metadata(self, entity_name: str, records_loaded: int, 
                         duration_seconds: float):
        """
        Log metadata about the load for monitoring and analytics.
        
        Args:
            entity_name: Name of the entity
            records_loaded: Number of records loaded
            duration_seconds: Time taken for the load
        """
        rate = records_loaded / duration_seconds if duration_seconds > 0 else 0
        
        logger.info(f"📊 Load Statistics for {entity_name}:")
        logger.info(f"   Records Loaded: {records_loaded:,}")
        logger.info(f"   Duration: {duration_seconds:.2f} seconds")
        logger.info(f"   Load Rate: {rate:.2f} records/second")
        
        # Update watermark with this metadata
        self.update_watermark(entity_name, datetime.now(), 
                            records_loaded, duration_seconds)


if __name__ == "__main__":
    # Test the incremental manager
    manager = IncrementalManager()
    
    # Test getting watermark
    last_load = manager.get_last_load_timestamp('orders')
    print(f"Last load for orders: {last_load}")
    
    # Test updating watermark
    manager.update_watermark('orders', datetime.now(), 100, 5.5)
    
    # Test getting date range
    date_range = manager.get_incremental_date_range('orders')
    print(f"Date range: {date_range}")
