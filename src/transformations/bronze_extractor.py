"""
Bronze Layer Extraction Module

Extracts raw data from Salla API and Odoo API and loads into Bronze layer tables.
"""

import logging
import json
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime

from src.api.salla_connector import SallaAPIConnector
from src.api.odoo_connector import OdooAPIConnector
from src.database.snowflake_connector import SnowflakeConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BronzeExtractor:
    """
    Handles extraction of raw data from Salla API and Odoo API into Bronze layer.
    """
    
    def __init__(self):
        self.salla_api = SallaAPIConnector()
        self.snowflake = SnowflakeConnector()
        # Odoo connector is initialised lazily to avoid failures when the
        # ODOO_API_TOKEN env variable is not set (e.g. Salla-only deployments).
        self._odoo_api: Optional[OdooAPIConnector] = None

    @property
    def odoo_api(self) -> OdooAPIConnector:
        """Lazy-initialised Odoo API connector."""
        if self._odoo_api is None:
            self._odoo_api = OdooAPIConnector()
        return self._odoo_api
    
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

    # ------------------------------------------------------------------
    # Odoo extraction methods
    # ------------------------------------------------------------------

    def extract_odoo_orders(self, order_names: List[str]) -> int:
        """
        Extract Odoo sale orders (and their lines) and load them to the
        bronze_odoo_orders and bronze_odoo_order_lines tables.

        Args:
            order_names: List of order references to fetch (e.g. ['S118658'])

        Returns:
            Number of order records loaded
        """
        logger.info("Starting Odoo orders extraction to Bronze layer")

        try:
            responses = self.odoo_api.fetch_sale_orders(order_names)

            if not responses:
                logger.warning("No Odoo orders returned")
                return 0

            orders: List[Dict] = []
            lines: List[Dict] = []

            for resp in responses:
                order = self.odoo_api.extract_order(resp)
                if order:
                    orders.append(order)
                lines.extend(self.odoo_api.extract_order_lines(resp))

            orders_df = self._prepare_odoo_orders_dataframe(orders)
            lines_df = self._prepare_odoo_order_lines_dataframe(lines)

            with self.snowflake as sf:
                sf.load_dataframe(
                    orders_df, 'BRONZE.bronze_odoo_orders', if_exists='append'
                )
                if not lines_df.empty:
                    sf.load_dataframe(
                        lines_df, 'BRONZE.bronze_odoo_order_lines',
                        if_exists='append'
                    )

            logger.info(
                f"Successfully loaded {len(orders_df)} Odoo orders "
                f"and {len(lines_df)} order lines to Bronze layer"
            )
            return len(orders_df)

        except Exception as e:
            logger.error(f"Odoo orders extraction failed: {str(e)}")
            raise

    def _prepare_odoo_orders_dataframe(self, orders: List[Dict]) -> pd.DataFrame:
        """Prepare Odoo orders data for Bronze layer."""
        df = pd.DataFrame(orders)

        # Serialise any nested structures
        for col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )

        # Parse date fields
        for col in ['date_order', 'ibq_salla_order_date', 'ibq_salla_order_update_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Store full raw JSON alongside typed columns
        df['raw_data'] = [json.dumps(o) for o in orders] if orders else []
        df['loaded_at'] = datetime.now()
        df['source_system'] = 'ODOO_API'

        return df

    def _prepare_odoo_order_lines_dataframe(self, lines: List[Dict]) -> pd.DataFrame:
        """Prepare Odoo order lines data for Bronze layer."""
        if not lines:
            return pd.DataFrame()

        df = pd.DataFrame(lines)

        for col in df.columns:
            df[col] = df[col].apply(
                lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
            )

        df['raw_data'] = [json.dumps(ln) for ln in lines]
        df['loaded_at'] = datetime.now()
        df['source_system'] = 'ODOO_API'

        return df


if __name__ == "__main__":
    # Example usage
    extractor = BronzeExtractor()
    
    # Extract data (limited to 1 page for testing)
    extractor.extract_orders(max_pages=1)
    extractor.extract_customers(max_pages=1)
    extractor.extract_products(max_pages=1)
