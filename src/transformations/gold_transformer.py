"""
Gold Layer Transformation Module

Transforms data from Silver to Gold layer (dimensional model).
"""

import logging
import pandas as pd
from datetime import datetime, timedelta

from src.database.snowflake_connector import SnowflakeConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoldTransformer:
    """
    Handles transformation of data from Silver to Gold layer (dimensional model).
    """
    
    def __init__(self):
        self.snowflake = SnowflakeConnector()
    
    def load_dim_customers(self) -> int:
        """
        Load dimension table for customers (SCD Type 2).
        
        Returns:
            Number of records loaded
        """
        logger.info("Loading gold_dim_customers")
        
        try:
            with self.snowflake as sf:
                # Get new/updated customers
                query = """
                    SELECT 
                        customer_id,
                        full_name,
                        first_name,
                        last_name,
                        email,
                        mobile,
                        country,
                        city,
                        gender,
                        age_group,
                        customer_status,
                        registration_date,
                        last_updated
                    FROM SILVER.silver_customers
                    WHERE customer_id NOT IN (
                        SELECT customer_id 
                        FROM GOLD.gold_dim_customers 
                        WHERE is_current = TRUE
                    )
                """
                
                new_customers = sf.execute_query(query)
                
                if not new_customers:
                    logger.info("No new customers to load")
                    return 0
                
                df = pd.DataFrame(new_customers)
                
                # Add SCD Type 2 fields
                df['effective_date'] = datetime.now()
                df['expiration_date'] = datetime(9999, 12, 31)
                df['is_current'] = True
                df['created_at'] = datetime.now()
                df['updated_at'] = datetime.now()
                
                # Load to dimension table
                sf.load_dataframe(df, 'GOLD.gold_dim_customers', if_exists='append')
                
                logger.info(f"Successfully loaded {len(df)} customers to Gold dimension")
                return len(df)
                
        except Exception as e:
            logger.error(f"Customer dimension load failed: {str(e)}")
            raise
    
    def load_dim_products(self) -> int:
        """
        Load dimension table for products (SCD Type 2).
        
        Returns:
            Number of records loaded
        """
        logger.info("Loading gold_dim_products")
        
        try:
            with self.snowflake as sf:
                # Get new/updated products
                query = """
                    SELECT 
                        product_id,
                        product_name,
                        product_description,
                        sku,
                        product_type,
                        product_status,
                        regular_price,
                        sale_price,
                        discount_percentage,
                        weight,
                        weight_unit,
                        is_active,
                        is_taxable,
                        requires_shipping
                    FROM SILVER.silver_products
                    WHERE product_id NOT IN (
                        SELECT product_id 
                        FROM GOLD.gold_dim_products 
                        WHERE is_current = TRUE
                    )
                """
                
                new_products = sf.execute_query(query)
                
                if not new_products:
                    logger.info("No new products to load")
                    return 0
                
                df = pd.DataFrame(new_products)
                
                # Add SCD Type 2 fields
                df['effective_date'] = datetime.now()
                df['expiration_date'] = datetime(9999, 12, 31)
                df['is_current'] = True
                df['created_at'] = datetime.now()
                df['updated_at'] = datetime.now()
                
                # Load to dimension table
                sf.load_dataframe(df, 'GOLD.gold_dim_products', if_exists='append')
                
                logger.info(f"Successfully loaded {len(df)} products to Gold dimension")
                return len(df)
                
        except Exception as e:
            logger.error(f"Product dimension load failed: {str(e)}")
            raise
    
    def load_dim_date(self, start_year: int = 2020, end_year: int = 2030) -> int:
        """
        Load date dimension table.
        
        Args:
            start_year: Start year for date dimension
            end_year: End year for date dimension
            
        Returns:
            Number of records loaded
        """
        logger.info("Loading gold_dim_date")
        
        try:
            with self.snowflake as sf:
                # Check if already populated
                existing = sf.execute_query("SELECT COUNT(*) as cnt FROM GOLD.gold_dim_date")
                # Handle case-insensitive column name
                count_key = 'CNT' if 'CNT' in existing[0] else 'cnt'
                if existing and existing[0].get(count_key, 0) > 0:
                    logger.info("Date dimension already populated")
                    return 0
                
                # Generate date range
                dates = pd.date_range(
                    start=f'{start_year}-01-01',
                    end=f'{end_year}-12-31',
                    freq='D'
                )
                
                date_data = []
                for date in dates:
                    date_data.append({
                        'date_key': int(date.strftime('%Y%m%d')),
                        'full_date': date,
                        'day_of_week': date.dayofweek + 1,
                        'day_name': date.strftime('%A'),
                        'day_of_month': date.day,
                        'day_of_year': date.dayofyear,
                        'week_of_year': date.isocalendar()[1],
                        'month_number': date.month,
                        'month_name': date.strftime('%B'),
                        'quarter': (date.month - 1) // 3 + 1,
                        'year': date.year,
                        'is_weekend': date.dayofweek >= 5,
                        'is_holiday': False,  # Can be enhanced with holiday calendar
                        'fiscal_year': date.year if date.month >= 1 else date.year - 1,
                        'fiscal_quarter': (date.month - 1) // 3 + 1
                    })
                
                df = pd.DataFrame(date_data)
                
                # Load to dimension table
                sf.load_dataframe(df, 'GOLD.gold_dim_date', if_exists='append')
                
                logger.info(f"Successfully loaded {len(df)} dates to Gold dimension")
                return len(df)
                
        except Exception as e:
            logger.error(f"Date dimension load failed: {str(e)}")
            raise
    
    def load_dim_payment_methods(self) -> int:
        """Load payment methods dimension from orders."""
        logger.info("Loading gold_dim_payment_method")
        
        try:
            with self.snowflake as sf:
                # Get unique payment methods
                query = """
                    SELECT DISTINCT 
                        payment_method as payment_method_name,
                        'Online' as payment_type
                    FROM SILVER.silver_orders
                    WHERE payment_method IS NOT NULL
                    AND payment_method NOT IN (
                        SELECT payment_method_name FROM GOLD.gold_dim_payment_method
                    )
                """
                
                new_methods = sf.execute_query(query)
                
                if not new_methods:
                    logger.info("No new payment methods to load")
                    return 0
                
                df = pd.DataFrame(new_methods)
                df['is_active'] = True
                df['created_at'] = datetime.now()
                
                sf.load_dataframe(df, 'GOLD.gold_dim_payment_method', if_exists='append')
                
                logger.info(f"Successfully loaded {len(df)} payment methods")
                return len(df)
                
        except Exception as e:
            logger.error(f"Payment method dimension load failed: {str(e)}")
            raise
    
    def load_dim_shipping_methods(self) -> int:
        """Load shipping methods dimension from orders."""
        logger.info("Loading gold_dim_shipping_method")
        
        try:
            with self.snowflake as sf:
                # Get unique shipping methods
                query = """
                    SELECT DISTINCT 
                        shipping_method as shipping_method_name,
                        'Standard' as shipping_type
                    FROM SILVER.silver_orders
                    WHERE shipping_method IS NOT NULL
                    AND shipping_method NOT IN (
                        SELECT shipping_method_name FROM GOLD.gold_dim_shipping_method
                    )
                """
                
                new_methods = sf.execute_query(query)
                
                if not new_methods:
                    logger.info("No new shipping methods to load")
                    return 0
                
                df = pd.DataFrame(new_methods)
                df['is_active'] = True
                df['created_at'] = datetime.now()
                
                sf.load_dataframe(df, 'GOLD.gold_dim_shipping_method', if_exists='append')
                
                logger.info(f"Successfully loaded {len(df)} shipping methods")
                return len(df)
                
        except Exception as e:
            logger.error(f"Shipping method dimension load failed: {str(e)}")
            raise
    
    def load_fact_orders(self) -> int:
        """
        Load fact table for orders.
        
        Returns:
            Number of records loaded
        """
        logger.info("Loading gold_fact_orders")
        
        try:
            with self.snowflake as sf:
                # Get new orders with dimension keys
                query = """
                    SELECT 
                        o.order_id,
                        o.reference_id,
                        c.customer_key,
                        TO_NUMBER(TO_CHAR(o.order_date, 'YYYYMMDD')) as order_date_key,
                        pm.payment_method_key,
                        sm.shipping_method_key,
                        o.order_status,
                        o.items_count,
                        o.subtotal_amount,
                        o.discount_amount,
                        o.tax_amount,
                        o.shipping_cost,
                        o.total_amount,
                        o.currency,
                        o.coupon_code,
                        o.shipping_country,
                        o.shipping_city,
                        o.order_date as order_created_at,
                        o.updated_at as order_updated_at
                    FROM SILVER.silver_orders o
                    LEFT JOIN GOLD.gold_dim_customers c 
                        ON o.customer_id = c.customer_id AND c.is_current = TRUE
                    LEFT JOIN GOLD.gold_dim_payment_method pm 
                        ON o.payment_method = pm.payment_method_name
                    LEFT JOIN GOLD.gold_dim_shipping_method sm 
                        ON o.shipping_method = sm.shipping_method_name
                    WHERE o.order_id NOT IN (
                        SELECT order_id FROM GOLD.gold_fact_orders
                    )
                """
                
                new_orders = sf.execute_query(query)
                
                if not new_orders:
                    logger.info("No new orders to load")
                    return 0
                
                df = pd.DataFrame(new_orders)
                df['loaded_at'] = datetime.now()
                
                # Load to fact table
                sf.load_dataframe(df, 'GOLD.gold_fact_orders', if_exists='append')
                
                logger.info(f"Successfully loaded {len(df)} orders to Gold fact table")
                return len(df)
                
        except Exception as e:
            logger.error(f"Fact orders load failed: {str(e)}")
            raise
    
    def transform_all(self):
        """Execute all Gold layer transformations in order."""
        logger.info("Starting complete Gold layer transformation")
        
        # Load dimensions first
        self.load_dim_date()
        self.load_dim_customers()
        self.load_dim_products()
        self.load_dim_payment_methods()
        self.load_dim_shipping_methods()
        
        # Load facts
        self.load_fact_orders()
        
        logger.info("Completed Gold layer transformation")


if __name__ == "__main__":
    # Example usage
    transformer = GoldTransformer()
    transformer.transform_all()
