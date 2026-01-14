"""
Silver Layer Transformation Module

Transforms and cleanses data from Bronze to Silver layer.
"""

import logging
import json
from typing import Dict, Any
import pandas as pd
from datetime import datetime

from src.database.snowflake_connector import SnowflakeConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SilverTransformer:
    """
    Handles transformation of data from Bronze to Silver layer.
    """
    
    def __init__(self):
        self.snowflake = SnowflakeConnector()
    
    def transform_orders(self) -> int:
        """
        Transform orders from Bronze to Silver layer.
        
        Returns:
            Number of records transformed
        """
        logger.info("Starting orders transformation to Silver layer")
        
        try:
            with self.snowflake as sf:
                # Extract from Bronze
                query = """
                    SELECT * FROM BRONZE.bronze_orders
                    WHERE id NOT IN (SELECT order_id FROM SILVER.silver_orders)
                    ORDER BY created_at
                """
                
                bronze_data = sf.execute_query(query)
                
                if not bronze_data:
                    logger.info("No new orders to transform")
                    return 0
                
                df = pd.DataFrame(bronze_data)
                
                # Transform data
                transformed_df = self._clean_orders(df)
                
                # Load to Silver
                sf.load_dataframe(transformed_df, 'SILVER.silver_orders', if_exists='append')
                
                logger.info(f"Successfully transformed {len(transformed_df)} orders to Silver layer")
                return len(transformed_df)
                
        except Exception as e:
            logger.error(f"Orders transformation failed: {str(e)}")
            raise
    
    def transform_customers(self) -> int:
        """
        Transform customers from Bronze to Silver layer.
        
        Returns:
            Number of records transformed
        """
        logger.info("Starting customers transformation to Silver layer")
        
        try:
            with self.snowflake as sf:
                # Extract from Bronze
                query = """
                    SELECT * FROM BRONZE.bronze_customers
                    WHERE id NOT IN (SELECT customer_id FROM SILVER.silver_customers)
                    ORDER BY created_at
                """
                
                bronze_data = sf.execute_query(query)
                
                if not bronze_data:
                    logger.info("No new customers to transform")
                    return 0
                
                df = pd.DataFrame(bronze_data)
                
                # Transform data
                transformed_df = self._clean_customers(df)
                
                # Load to Silver
                sf.load_dataframe(transformed_df, 'SILVER.silver_customers', if_exists='append')
                
                logger.info(f"Successfully transformed {len(transformed_df)} customers to Silver layer")
                return len(transformed_df)
                
        except Exception as e:
            logger.error(f"Customers transformation failed: {str(e)}")
            raise
    
    def transform_products(self) -> int:
        """
        Transform products from Bronze to Silver layer.
        
        Returns:
            Number of records transformed
        """
        logger.info("Starting products transformation to Silver layer")
        
        try:
            with self.snowflake as sf:
                # Extract from Bronze
                query = """
                    SELECT * FROM BRONZE.bronze_products
                    WHERE id NOT IN (SELECT product_id FROM SILVER.silver_products)
                    ORDER BY created_at
                """
                
                bronze_data = sf.execute_query(query)
                
                if not bronze_data:
                    logger.info("No new products to transform")
                    return 0
                
                df = pd.DataFrame(bronze_data)
                
                # Transform data
                transformed_df = self._clean_products(df)
                
                # Load to Silver
                sf.load_dataframe(transformed_df, 'SILVER.silver_products', if_exists='append')
                
                logger.info(f"Successfully transformed {len(transformed_df)} products to Silver layer")
                return len(transformed_df)
                
        except Exception as e:
            logger.error(f"Products transformation failed: {str(e)}")
            raise
    
    def _clean_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and transform orders data."""
        # Rename columns
        df = df.rename(columns={
            'id': 'order_id',
            'status': 'order_status',
            'created_at': 'order_date'
        })
        
        # Extract shipping address fields
        if 'shipping_address' in df.columns:
            df['shipping_country'] = df['shipping_address'].apply(
                lambda x: self._extract_json_field(x, 'country')
            )
            df['shipping_city'] = df['shipping_address'].apply(
                lambda x: self._extract_json_field(x, 'city')
            )
            df['shipping_address_line'] = df['shipping_address'].apply(
                lambda x: self._extract_json_field(x, 'address')
            )
            df['shipping_postal_code'] = df['shipping_address'].apply(
                lambda x: self._extract_json_field(x, 'postal_code')
            )
        
        # Calculate items count
        if 'items' in df.columns:
            df['items_count'] = df['items'].apply(
                lambda x: len(json.loads(x)) if isinstance(x, str) and x else 0
            )
        
        # Rename amount to subtotal
        if 'amount' in df.columns:
            df['subtotal_amount'] = df['amount']
        
        # Remove nulls and clean data
        df = df.dropna(subset=['order_id'])
        
        # Standardize status values
        if 'order_status' in df.columns:
            df['order_status'] = df['order_status'].str.upper().str.strip()
        
        # Add processed timestamp
        df['processed_at'] = datetime.now()
        
        # Select and order columns
        columns = [
            'order_id', 'reference_id', 'order_status', 'order_date',
            'customer_id', 'customer_name', 'customer_email', 'customer_mobile',
            'payment_method', 'shipping_method',
            'shipping_country', 'shipping_city', 'shipping_address_line', 'shipping_postal_code',
            'subtotal_amount', 'discount_amount', 'tax_amount', 'shipping_cost', 'total_amount',
            'currency', 'coupon_code', 'notes', 'items_count',
            'created_at', 'updated_at', 'processed_at'
        ]
        
        # Only include columns that exist
        columns = [col for col in columns if col in df.columns]
        
        return df[columns]
    
    def _clean_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and transform customers data."""
        # Rename columns
        df = df.rename(columns={
            'id': 'customer_id',
            'status': 'customer_status',
            'created_at': 'registration_date',
            'updated_at': 'last_updated',
            'avatar': 'avatar_url'
        })
        
        # Create full name
        df['full_name'] = df.apply(
            lambda row: f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
            axis=1
        )
        
        # Calculate age group from birthday
        if 'birthday' in df.columns:
            df['age_group'] = df['birthday'].apply(self._calculate_age_group)
        
        # Remove nulls and duplicates
        df = df.dropna(subset=['customer_id'])
        df = df.drop_duplicates(subset=['customer_id'], keep='last')
        
        # Standardize gender
        if 'gender' in df.columns:
            df['gender'] = df['gender'].str.upper().str.strip()
        
        # Clean email
        if 'email' in df.columns:
            df['email'] = df['email'].str.lower().str.strip()
        
        # Add processed timestamp
        df['processed_at'] = datetime.now()
        
        # Select and order columns
        columns = [
            'customer_id', 'full_name', 'first_name', 'last_name',
            'email', 'mobile', 'mobile_code',
            'country', 'city', 'gender', 'birthday', 'age_group',
            'customer_status', 'avatar_url',
            'registration_date', 'last_updated', 'processed_at'
        ]
        
        # Only include columns that exist
        columns = [col for col in columns if col in df.columns]
        
        return df[columns]
    
    def _clean_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and transform products data."""
        # Rename columns
        df = df.rename(columns={
            'id': 'product_id',
            'name': 'product_name',
            'description': 'product_description',
            'price': 'regular_price',
            'status': 'product_status',
            'type': 'product_type',
            'quantity': 'quantity_available',
            'unlimited_quantity': 'is_unlimited',
            'metadata_title': 'meta_title',
            'metadata_description': 'meta_description'
        })
        
        # Calculate profit margin (vectorized for performance)
        if 'regular_price' in df.columns and 'cost_price' in df.columns:
            df['profit_margin'] = 0.0
            mask = df['regular_price'] > 0
            df.loc[mask, 'profit_margin'] = (
                (df.loc[mask, 'regular_price'] - df.loc[mask, 'cost_price']) / 
                df.loc[mask, 'regular_price'] * 100
            )
        
        # Calculate discount percentage (vectorized for performance)
        if 'regular_price' in df.columns and 'sale_price' in df.columns:
            df['discount_percentage'] = 0.0
            mask = df['regular_price'] > 0
            df.loc[mask, 'discount_percentage'] = (
                (df.loc[mask, 'regular_price'] - df.loc[mask, 'sale_price']) / 
                df.loc[mask, 'regular_price'] * 100
            )
        
        # Create is_active flag (vectorized for performance)
        if 'product_status' in df.columns:
            df['is_active'] = df['product_status'].str.upper().isin(
                ['ACTIVE', 'AVAILABLE', 'IN_STOCK']
            ).fillna(False)
        
        # Remove nulls
        df = df.dropna(subset=['product_id'])
        
        # Standardize status
        if 'product_status' in df.columns:
            df['product_status'] = df['product_status'].str.upper().str.strip()
        
        # Add processed timestamp
        df['processed_at'] = datetime.now()
        
        # Select and order columns
        columns = [
            'product_id', 'product_name', 'product_description',
            'regular_price', 'sale_price', 'cost_price', 'profit_margin', 'discount_percentage',
            'sku', 'quantity_available', 'is_unlimited',
            'product_type', 'product_status', 'is_active',
            'weight', 'weight_unit',
            'with_tax', 'is_taxable', 'requires_shipping',
            'meta_title', 'meta_description',
            'created_at', 'updated_at', 'processed_at'
        ]
        
        # Only include columns that exist
        columns = [col for col in columns if col in df.columns]
        
        return df[columns]
    
    @staticmethod
    def _extract_json_field(json_str: Any, field: str) -> Any:
        """Extract field from JSON string."""
        try:
            if isinstance(json_str, str):
                data = json.loads(json_str)
                return data.get(field)
            elif isinstance(json_str, dict):
                return json_str.get(field)
            return None
        except:
            return None
    
    @staticmethod
    def _calculate_age_group(birthday) -> str:
        """Calculate age group from birthday."""
        if pd.isna(birthday):
            return 'Unknown'
        
        try:
            age = (datetime.now() - pd.to_datetime(birthday)).days // 365
            
            if age < 18:
                return 'Under 18'
            elif age < 25:
                return '18-24'
            elif age < 35:
                return '25-34'
            elif age < 45:
                return '35-44'
            elif age < 55:
                return '45-54'
            elif age < 65:
                return '55-64'
            else:
                return '65+'
        except:
            return 'Unknown'


if __name__ == "__main__":
    # Example usage
    transformer = SilverTransformer()
    
    transformer.transform_orders()
    transformer.transform_customers()
    transformer.transform_products()
