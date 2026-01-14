"""
Bronze Layer Extraction Module

Extracts raw data from Salla API and loads into Bronze layer tables.
"""

import logging
import json
from typing import List, Dict
import pandas as pd
from datetime import datetime

from src.api.salla_connector import SallaAPIConnector
from src.database.snowflake_connector import SnowflakeConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BronzeExtractor:
    """
    Handles extraction of raw data from Salla API into Bronze layer.
    """
    
    def __init__(self):
        self.salla_api = SallaAPIConnector()
        self.snowflake = SnowflakeConnector()
    
    def extract_orders(self, max_pages: int = None) -> int:
        """
        Extract orders from Salla API and load to bronze_orders table.
        
        Args:
            max_pages: Maximum number of pages to extract
            
        Returns:
            Number of records loaded
        """
        logger.info("Starting orders extraction to Bronze layer")
        
        try:
            # Fetch all orders
            orders = self.salla_api.fetch_all_pages('orders', max_pages=max_pages)
            
            if not orders:
                logger.warning("No orders found")
                return 0
            
            # Transform to DataFrame
            df = self._prepare_orders_dataframe(orders)
            
            # Load to Snowflake
            with self.snowflake as sf:
                sf.load_dataframe(df, 'BRONZE.bronze_orders', if_exists='append')
            
            logger.info(f"Successfully loaded {len(df)} orders to Bronze layer")
            return len(df)
            
        except Exception as e:
            logger.error(f"Orders extraction failed: {str(e)}")
            raise
    
    def extract_customers(self, max_pages: int = None) -> int:
        """
        Extract customers from Salla API and load to bronze_customers table.
        
        Args:
            max_pages: Maximum number of pages to extract
            
        Returns:
            Number of records loaded
        """
        logger.info("Starting customers extraction to Bronze layer")
        
        try:
            # Fetch all customers
            customers = self.salla_api.fetch_all_pages('customers', max_pages=max_pages)
            
            if not customers:
                logger.warning("No customers found")
                return 0
            
            # Transform to DataFrame
            df = self._prepare_customers_dataframe(customers)
            
            # Load to Snowflake
            with self.snowflake as sf:
                sf.load_dataframe(df, 'BRONZE.bronze_customers', if_exists='append')
            
            logger.info(f"Successfully loaded {len(df)} customers to Bronze layer")
            return len(df)
            
        except Exception as e:
            logger.error(f"Customers extraction failed: {str(e)}")
            raise
    
    def extract_products(self, max_pages: int = None) -> int:
        """
        Extract products from Salla API and load to bronze_products table.
        
        Args:
            max_pages: Maximum number of pages to extract
            
        Returns:
            Number of records loaded
        """
        logger.info("Starting products extraction to Bronze layer")
        
        try:
            # Fetch all products
            products = self.salla_api.fetch_all_pages('products', max_pages=max_pages)
            
            if not products:
                logger.warning("No products found")
                return 0
            
            # Transform to DataFrame
            df = self._prepare_products_dataframe(products)
            
            # Load to Snowflake
            with self.snowflake as sf:
                sf.load_dataframe(df, 'BRONZE.bronze_products', if_exists='append')
            
            logger.info(f"Successfully loaded {len(df)} products to Bronze layer")
            return len(df)
            
        except Exception as e:
            logger.error(f"Products extraction failed: {str(e)}")
            raise
    
    def _prepare_orders_dataframe(self, orders: List[Dict]) -> pd.DataFrame:
        """Prepare orders data for Bronze layer."""
        df = pd.DataFrame(orders)
        
        # Convert complex objects to JSON strings for VARIANT columns
        if 'shipping_address' in df.columns:
            df['shipping_address'] = df['shipping_address'].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )
        
        if 'items' in df.columns:
            df['items'] = df['items'].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )
        
        # Convert timestamps
        for col in ['created_at', 'updated_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Add metadata
        df['loaded_at'] = datetime.now()
        df['source_system'] = 'SALLA_API'
        
        return df
    
    def _prepare_customers_dataframe(self, customers: List[Dict]) -> pd.DataFrame:
        """Prepare customers data for Bronze layer."""
        df = pd.DataFrame(customers)
        
        # Convert complex objects to JSON strings
        if 'addresses' in df.columns:
            df['addresses'] = df['addresses'].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )
        
        # Convert timestamps
        for col in ['created_at', 'updated_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        if 'birthday' in df.columns:
            df['birthday'] = pd.to_datetime(df['birthday'], errors='coerce')
        
        # Add metadata
        df['loaded_at'] = datetime.now()
        df['source_system'] = 'SALLA_API'
        
        return df
    
    def _prepare_products_dataframe(self, products: List[Dict]) -> pd.DataFrame:
        """Prepare products data for Bronze layer."""
        df = pd.DataFrame(products)
        
        # Convert complex objects to JSON strings
        for col in ['images', 'categories', 'options']:
            if col in df.columns:
                df[col] = df[col].apply(
                    lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
                )
        
        # Convert timestamps
        for col in ['created_at', 'updated_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Add metadata
        df['loaded_at'] = datetime.now()
        df['source_system'] = 'SALLA_API'
        
        return df


if __name__ == "__main__":
    # Example usage
    extractor = BronzeExtractor()
    
    # Extract data (limited to 1 page for testing)
    extractor.extract_orders(max_pages=1)
    extractor.extract_customers(max_pages=1)
    extractor.extract_products(max_pages=1)
