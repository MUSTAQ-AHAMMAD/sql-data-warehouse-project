"""
Universal Transformer Module

Database-agnostic transformer that works with any backend via factory pattern.
Executes transformation queries with proper error handling and logging.
"""

import os
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv

from src.database.database_factory import get_database_connector, get_database_type

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniversalTransformer:
    """
    Universal transformer that works with any database backend.
    
    Executes SQL transformations using the database factory pattern,
    providing a consistent interface regardless of the underlying database.
    """
    
    def __init__(self):
        """Initialize transformer with database connection."""
        self.db = get_database_connector()
        self.db_type = get_database_type()
        logger.info(f"Initialized Universal Transformer for {self.db_type}")
    
    def execute_transformation(self, transformation_name: str, 
                              query: str, params: Optional[tuple] = None) -> int:
        """
        Execute a single transformation query.
        
        Args:
            transformation_name: Descriptive name for logging
            query: SQL query to execute
            params: Optional query parameters
            
        Returns:
            Number of rows affected (if applicable)
            
        Raises:
            Exception: If transformation fails
        """
        logger.info(f"Starting transformation: {transformation_name}")
        
        try:
            with self.db as conn:
                result = conn.execute_query(query, params)
                
                # Try to get row count from result
                rows_affected = len(result) if result else 0
                
                logger.info(f"✅ Completed {transformation_name}: {rows_affected} rows")
                return rows_affected
                
        except Exception as e:
            logger.error(f"❌ Transformation '{transformation_name}' failed: {str(e)}")
            raise
    
    def execute_transformation_batch(self, transformations: List[Dict]) -> Dict[str, int]:
        """
        Execute multiple transformations in sequence.
        
        Args:
            transformations: List of dicts with 'name' and 'query' keys
            
        Returns:
            Dictionary mapping transformation names to row counts
            
        Example:
            transformations = [
                {'name': 'Clean Orders', 'query': 'UPDATE ...'},
                {'name': 'Aggregate Sales', 'query': 'INSERT ...'}
            ]
        """
        results = {}
        
        logger.info(f"Starting batch of {len(transformations)} transformations")
        
        for i, transform in enumerate(transformations, 1):
            name = transform.get('name', f'Transformation_{i}')
            query = transform['query']
            params = transform.get('params')
            
            try:
                rows = self.execute_transformation(name, query, params)
                results[name] = rows
                
            except Exception as e:
                logger.error(f"Batch stopped at transformation {i}/{len(transformations)}: {name}")
                results[name] = -1  # Indicate failure
                raise
        
        logger.info(f"✅ Completed batch: {len(transformations)} transformations")
        return results
    
    def transform_bronze_to_silver(self, entity_type: str) -> int:
        """
        Transform data from Bronze to Silver layer for a specific entity.
        
        Args:
            entity_type: Type of entity ('orders', 'customers', 'products')
            
        Returns:
            Number of records transformed
        """
        logger.info(f"Transforming {entity_type} from Bronze to Silver")
        
        # Define transformation queries based on entity type
        if entity_type == 'orders':
            query = """
                INSERT INTO SILVER.silver_orders (
                    order_id, reference_id, status, amount, currency,
                    customer_id, customer_name, payment_method, 
                    order_date, created_at, updated_at, source_system
                )
                SELECT 
                    id, reference_id, status, amount, currency,
                    customer_id, customer_name, payment_method,
                    created_at, loaded_at, GETDATE(), source_system
                FROM BRONZE.bronze_orders
                WHERE id NOT IN (SELECT order_id FROM SILVER.silver_orders)
            """
        elif entity_type == 'customers':
            query = """
                INSERT INTO SILVER.silver_customers (
                    customer_id, full_name, first_name, last_name,
                    email, mobile, country, city, gender,
                    registration_date, created_at, updated_at, source_system
                )
                SELECT 
                    id, 
                    CONCAT(first_name, ' ', last_name) as full_name,
                    first_name, last_name, email, mobile, country, city, gender,
                    created_at, loaded_at, GETDATE(), source_system
                FROM BRONZE.bronze_customers
                WHERE id NOT IN (SELECT customer_id FROM SILVER.silver_customers)
            """
        elif entity_type == 'products':
            query = """
                INSERT INTO SILVER.silver_products (
                    product_id, product_name, description, price, 
                    sale_price, cost_price, sku, quantity, status,
                    created_at, updated_at, source_system
                )
                SELECT 
                    id, name, description, price,
                    sale_price, cost_price, sku, quantity, status,
                    loaded_at, GETDATE(), source_system
                FROM BRONZE.bronze_products
                WHERE id NOT IN (SELECT product_id FROM SILVER.silver_products)
            """
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        return self.execute_transformation(
            f"Bronze to Silver: {entity_type}", 
            query
        )
    
    def transform_silver_to_gold(self, entity_type: str) -> int:
        """
        Transform data from Silver to Gold layer for dimensional modeling.
        
        Args:
            entity_type: Type of entity ('dim_customers', 'dim_products', 'fact_orders')
            
        Returns:
            Number of records transformed
        """
        logger.info(f"Transforming {entity_type} from Silver to Gold")
        
        # Define transformation queries based on entity type
        if entity_type == 'dim_customers':
            query = """
                INSERT INTO GOLD.gold_dim_customers (
                    customer_id, full_name, first_name, last_name,
                    email, mobile, country, city, gender,
                    registration_date, effective_date, expiration_date,
                    is_current, created_at, updated_at
                )
                SELECT 
                    customer_id, full_name, first_name, last_name,
                    email, mobile, country, city, gender,
                    registration_date, GETDATE(), '9999-12-31',
                    1, GETDATE(), GETDATE()
                FROM SILVER.silver_customers
                WHERE customer_id NOT IN (
                    SELECT customer_id FROM GOLD.gold_dim_customers 
                    WHERE is_current = 1
                )
            """
        elif entity_type == 'dim_products':
            query = """
                INSERT INTO GOLD.gold_dim_products (
                    product_id, product_name, description, price,
                    sale_price, cost_price, sku, category,
                    effective_date, expiration_date, is_current,
                    created_at, updated_at
                )
                SELECT 
                    product_id, product_name, description, price,
                    sale_price, cost_price, sku, 'General',
                    GETDATE(), '9999-12-31', 1,
                    GETDATE(), GETDATE()
                FROM SILVER.silver_products
                WHERE product_id NOT IN (
                    SELECT product_id FROM GOLD.gold_dim_products 
                    WHERE is_current = 1
                )
            """
        elif entity_type == 'fact_orders':
            query = """
                INSERT INTO GOLD.gold_fact_orders (
                    order_id, customer_id, product_id, order_date,
                    quantity, unit_price, total_amount, currency,
                    status, payment_method, created_at
                )
                SELECT 
                    o.order_id, o.customer_id, 1 as product_id,
                    o.order_date, 1 as quantity, o.amount as unit_price,
                    o.amount as total_amount, o.currency,
                    o.status, o.payment_method, GETDATE()
                FROM SILVER.silver_orders o
                WHERE o.order_id NOT IN (
                    SELECT order_id FROM GOLD.gold_fact_orders
                )
            """
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")
        
        return self.execute_transformation(
            f"Silver to Gold: {entity_type}",
            query
        )
    
    def run_custom_query(self, query: str, description: str = "Custom Query") -> int:
        """
        Run a custom transformation query.
        
        Args:
            query: SQL query to execute
            description: Description for logging
            
        Returns:
            Number of rows affected
        """
        return self.execute_transformation(description, query)


if __name__ == "__main__":
    # Test the universal transformer
    transformer = UniversalTransformer()
    
    # Test Bronze to Silver transformation
    try:
        rows = transformer.transform_bronze_to_silver('orders')
        print(f"✅ Transformed {rows} orders from Bronze to Silver")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test Silver to Gold transformation
    try:
        rows = transformer.transform_silver_to_gold('dim_customers')
        print(f"✅ Transformed {rows} customers to Gold dimension")
    except Exception as e:
        print(f"❌ Error: {e}")
