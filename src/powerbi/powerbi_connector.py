"""
Power BI Connector Module

Creates optimized views for Power BI reporting and visualization.
Provides connection string helpers and view testing functionality.
"""

import os
import logging
from typing import List, Dict
from dotenv import load_dotenv

from src.database.database_factory import get_database_connector, get_database_type

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PowerBIConnector:
    """
    Creates and manages Power BI views for data visualization.
    
    Provides optimized views for common business intelligence scenarios:
    - Sales overview with daily metrics
    - Order details for transaction analysis
    - Product performance analytics
    - Customer analysis and segmentation
    """
    
    def __init__(self):
        """Initialize Power BI connector with database connection."""
        self.db = get_database_connector()
        self.db_type = get_database_type()
        logger.info(f"Initialized Power BI Connector for {self.db_type}")
    
    def create_powerbi_schema(self):
        """Create PowerBI schema if it doesn't exist."""
        try:
            with self.db as conn:
                # Check if schema exists
                check_query = """
                    SELECT COUNT(*) as cnt
                    FROM INFORMATION_SCHEMA.SCHEMATA
                    WHERE SCHEMA_NAME = 'PowerBI'
                """
                
                result = conn.execute_query(check_query)
                
                if result[0]['cnt'] == 0:
                    create_query = "CREATE SCHEMA PowerBI"
                    conn.execute_query(create_query)
                    logger.info("✅ Created PowerBI schema")
                else:
                    logger.info("PowerBI schema already exists")
                    
        except Exception as e:
            logger.error(f"Error creating PowerBI schema: {str(e)}")
            raise
    
    def create_sales_overview_view(self):
        """
        Create vw_Sales_Overview view for daily sales metrics.
        
        Provides aggregated daily sales data with key metrics:
        - Total sales amount
        - Number of orders
        - Number of unique customers
        - Average order value
        """
        logger.info("Creating vw_Sales_Overview view...")
        
        view_query = """
        IF OBJECT_ID('PowerBI.vw_Sales_Overview', 'V') IS NOT NULL
            DROP VIEW PowerBI.vw_Sales_Overview;
        """
        
        # Create view
        create_query = """
        CREATE VIEW PowerBI.vw_Sales_Overview AS
        SELECT 
            CAST(o.order_date AS DATE) as OrderDate,
            COUNT(DISTINCT o.order_id) as TotalOrders,
            COUNT(DISTINCT o.customer_id) as UniqueCustomers,
            SUM(o.amount) as TotalSales,
            AVG(o.amount) as AverageOrderValue,
            o.currency as Currency,
            COUNT(CASE WHEN o.status = 'completed' THEN 1 END) as CompletedOrders,
            COUNT(CASE WHEN o.status = 'pending' THEN 1 END) as PendingOrders,
            COUNT(CASE WHEN o.status = 'cancelled' THEN 1 END) as CancelledOrders
        FROM SILVER.silver_orders o
        GROUP BY CAST(o.order_date AS DATE), o.currency
        """
        
        try:
            with self.db as conn:
                conn.execute_query(view_query)
                conn.execute_query(create_query)
                logger.info("✅ Created vw_Sales_Overview")
        except Exception as e:
            logger.error(f"Error creating sales overview view: {str(e)}")
            raise
    
    def create_order_details_view(self):
        """
        Create vw_Order_Details view for individual order records.
        
        Provides detailed order information joined with customer data:
        - Order details
        - Customer information
        - Payment and shipping methods
        - Order status
        """
        logger.info("Creating vw_Order_Details view...")
        
        view_query = """
        IF OBJECT_ID('PowerBI.vw_Order_Details', 'V') IS NOT NULL
            DROP VIEW PowerBI.vw_Order_Details;
        """
        
        create_query = """
        CREATE VIEW PowerBI.vw_Order_Details AS
        SELECT 
            o.order_id as OrderID,
            o.reference_id as ReferenceID,
            o.order_date as OrderDate,
            o.status as OrderStatus,
            o.amount as Amount,
            o.currency as Currency,
            o.payment_method as PaymentMethod,
            c.customer_id as CustomerID,
            c.full_name as CustomerName,
            c.email as CustomerEmail,
            c.city as CustomerCity,
            c.country as CustomerCountry,
            o.created_at as CreatedAt,
            o.updated_at as UpdatedAt
        FROM SILVER.silver_orders o
        LEFT JOIN SILVER.silver_customers c ON o.customer_id = c.customer_id
        """
        
        try:
            with self.db as conn:
                conn.execute_query(view_query)
                conn.execute_query(create_query)
                logger.info("✅ Created vw_Order_Details")
        except Exception as e:
            logger.error(f"Error creating order details view: {str(e)}")
            raise
    
    def create_product_performance_view(self):
        """
        Create vw_Product_Performance view for product analytics.
        
        Provides product-level metrics:
        - Product details
        - Sales metrics
        - Inventory status
        - Pricing information
        """
        logger.info("Creating vw_Product_Performance view...")
        
        view_query = """
        IF OBJECT_ID('PowerBI.vw_Product_Performance', 'V') IS NOT NULL
            DROP VIEW PowerBI.vw_Product_Performance;
        """
        
        create_query = """
        CREATE VIEW PowerBI.vw_Product_Performance AS
        SELECT 
            p.product_id as ProductID,
            p.product_name as ProductName,
            p.sku as SKU,
            p.price as Price,
            p.sale_price as SalePrice,
            p.cost_price as CostPrice,
            p.quantity as CurrentStock,
            p.status as Status,
            CASE 
                WHEN p.quantity = 0 THEN 'Out of Stock'
                WHEN p.quantity < 10 THEN 'Low Stock'
                ELSE 'In Stock'
            END as StockStatus,
            CASE 
                WHEN p.sale_price IS NOT NULL 
                THEN ROUND((p.price - p.sale_price) / p.price * 100, 2)
                ELSE 0
            END as DiscountPercentage,
            CASE 
                WHEN p.sale_price IS NOT NULL THEN p.sale_price
                ELSE p.price
            END as EffectivePrice,
            p.created_at as CreatedAt,
            p.updated_at as UpdatedAt
        FROM SILVER.silver_products p
        """
        
        try:
            with self.db as conn:
                conn.execute_query(view_query)
                conn.execute_query(create_query)
                logger.info("✅ Created vw_Product_Performance")
        except Exception as e:
            logger.error(f"Error creating product performance view: {str(e)}")
            raise
    
    def create_customer_analysis_view(self):
        """
        Create vw_Customer_Analysis view for customer metrics.
        
        Provides customer-level analytics:
        - Customer demographics
        - Order history
        - Customer lifetime value
        - Segmentation data
        """
        logger.info("Creating vw_Customer_Analysis view...")
        
        view_query = """
        IF OBJECT_ID('PowerBI.vw_Customer_Analysis', 'V') IS NOT NULL
            DROP VIEW PowerBI.vw_Customer_Analysis;
        """
        
        create_query = """
        CREATE VIEW PowerBI.vw_Customer_Analysis AS
        SELECT 
            c.customer_id as CustomerID,
            c.full_name as CustomerName,
            c.first_name as FirstName,
            c.last_name as LastName,
            c.email as Email,
            c.mobile as Mobile,
            c.gender as Gender,
            c.city as City,
            c.country as Country,
            c.registration_date as RegistrationDate,
            COUNT(DISTINCT o.order_id) as TotalOrders,
            SUM(o.amount) as TotalSpent,
            AVG(o.amount) as AverageOrderValue,
            MAX(o.order_date) as LastOrderDate,
            MIN(o.order_date) as FirstOrderDate,
            DATEDIFF(day, c.registration_date, GETDATE()) as DaysSinceRegistration,
            CASE 
                WHEN COUNT(DISTINCT o.order_id) = 0 THEN 'Inactive'
                WHEN COUNT(DISTINCT o.order_id) = 1 THEN 'One-Time Buyer'
                WHEN COUNT(DISTINCT o.order_id) < 5 THEN 'Occasional Buyer'
                ELSE 'Regular Customer'
            END as CustomerSegment
        FROM SILVER.silver_customers c
        LEFT JOIN SILVER.silver_orders o ON c.customer_id = o.customer_id
        GROUP BY 
            c.customer_id, c.full_name, c.first_name, c.last_name,
            c.email, c.mobile, c.gender, c.city, c.country,
            c.registration_date
        """
        
        try:
            with self.db as conn:
                conn.execute_query(view_query)
                conn.execute_query(create_query)
                logger.info("✅ Created vw_Customer_Analysis")
        except Exception as e:
            logger.error(f"Error creating customer analysis view: {str(e)}")
            raise
    
    def create_all_views(self):
        """Create all Power BI views."""
        logger.info("=" * 80)
        logger.info("CREATING POWER BI VIEWS")
        logger.info("=" * 80)
        
        try:
            # Create PowerBI schema
            self.create_powerbi_schema()
            
            # Create all views
            self.create_sales_overview_view()
            self.create_order_details_view()
            self.create_product_performance_view()
            self.create_customer_analysis_view()
            
            logger.info("=" * 80)
            logger.info("✅ ALL POWER BI VIEWS CREATED SUCCESSFULLY")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Error creating Power BI views: {str(e)}")
            raise
    
    def test_views(self) -> Dict[str, int]:
        """
        Test all views and return row counts.
        
        Returns:
            Dictionary mapping view names to row counts
        """
        logger.info("Testing Power BI views...")
        
        views = [
            'PowerBI.vw_Sales_Overview',
            'PowerBI.vw_Order_Details',
            'PowerBI.vw_Product_Performance',
            'PowerBI.vw_Customer_Analysis'
        ]
        
        results = {}
        
        try:
            with self.db as conn:
                for view in views:
                    query = f"SELECT COUNT(*) as cnt FROM {view}"
                    result = conn.execute_query(query)
                    count = result[0]['cnt']
                    results[view] = count
                    logger.info(f"   {view}: {count} rows")
            
            logger.info("✅ All views tested successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error testing views: {str(e)}")
            raise
    
    def get_connection_string(self) -> str:
        """
        Get the connection string for Power BI Desktop.
        
        Returns:
            Connection string for the database
        """
        if self.db_type == 'sqlserver':
            server = os.getenv('SQLSERVER_HOST', 'localhost\\SQLEXPRESS')
            database = os.getenv('SQLSERVER_DATABASE', 'SALLA_DWH')
            
            conn_str = f"Server={server};Database={database};Trusted_Connection=yes;"
            
            logger.info("=" * 80)
            logger.info("POWER BI CONNECTION STRING")
            logger.info("=" * 80)
            logger.info(f"Server: {server}")
            logger.info(f"Database: {database}")
            logger.info(f"Connection String: {conn_str}")
            logger.info("=" * 80)
            
            return conn_str
            
        elif self.db_type == 'snowflake':
            account = os.getenv('SNOWFLAKE_ACCOUNT')
            warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
            database = os.getenv('SNOWFLAKE_DATABASE', 'SALLA_DWH')
            
            conn_str = f"Account={account};Warehouse={warehouse};Database={database}"
            
            logger.info("=" * 80)
            logger.info("POWER BI CONNECTION STRING (SNOWFLAKE)")
            logger.info("=" * 80)
            logger.info(f"Account: {account}")
            logger.info(f"Warehouse: {warehouse}")
            logger.info(f"Database: {database}")
            logger.info(f"Connection String: {conn_str}")
            logger.info("=" * 80)
            
            return conn_str
        
        return ""
    
    def list_available_views(self) -> List[str]:
        """
        List all available Power BI views.
        
        Returns:
            List of view names
        """
        try:
            with self.db as conn:
                query = """
                    SELECT TABLE_NAME 
                    FROM INFORMATION_SCHEMA.VIEWS 
                    WHERE TABLE_SCHEMA = 'PowerBI'
                    ORDER BY TABLE_NAME
                """
                
                result = conn.execute_query(query)
                views = [row['TABLE_NAME'] for row in result]
                
                logger.info("Available Power BI Views:")
                for view in views:
                    logger.info(f"   - PowerBI.{view}")
                
                return views
                
        except Exception as e:
            logger.error(f"Error listing views: {str(e)}")
            return []


if __name__ == "__main__":
    # Test the Power BI connector
    connector = PowerBIConnector()
    
    # Create all views
    try:
        connector.create_all_views()
        print("\n✅ Views created successfully")
    except Exception as e:
        print(f"\n❌ Error creating views: {e}")
    
    # Test views
    try:
        results = connector.test_views()
        print(f"\n📊 View row counts: {results}")
    except Exception as e:
        print(f"\n❌ Error testing views: {e}")
    
    # Get connection string
    try:
        conn_str = connector.get_connection_string()
        print(f"\n🔗 Connection String: {conn_str}")
    except Exception as e:
        print(f"\n❌ Error getting connection string: {e}")
    
    # List views
    try:
        views = connector.list_available_views()
        print(f"\n📋 Found {len(views)} Power BI views")
    except Exception as e:
        print(f"\n❌ Error listing views: {e}")
