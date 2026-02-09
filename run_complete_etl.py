"""
Complete ETL Pipeline Orchestrator
Runs Bronze → Silver → Gold with quality checks
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from src.transformations.bronze_extractor_production import ProductionBronzeExtractor
from src.database.database_factory import get_database_connector
from dotenv import load_dotenv

load_dotenv()


def run_bronze_layer():
    """Extract to Bronze"""
    print("\n" + "="*70)
    print("🥉 BRONZE LAYER - RAW DATA EXTRACTION")
    print("="*70)
    
    extractor = ProductionBronzeExtractor()
    orders_count = extractor.extract_orders()
    
    print(f"✅ Bronze Layer Complete: {orders_count} records")
    return orders_count


def run_silver_layer():
    """Transform to Silver"""
    print("\n" + "="*70)
    print("🥈 SILVER LAYER - DATA TRANSFORMATION")
    print("="*70)
    
    db = get_database_connector()
    
    with db as conn:
        # Transform orders
        query = """
            INSERT INTO silver.silver_orders 
            (order_id, customer_id, order_date, total_amount, status, processed_at)
            SELECT 
                order_id,
                JSON_VALUE(raw_data, '$.customer.id') as customer_id,
                CAST(JSON_VALUE(raw_data, '$.created_at') AS DATE) as order_date,
                CAST(JSON_VALUE(raw_data, '$.total.amount') AS DECIMAL(15,2)) as total_amount,
                JSON_VALUE(raw_data, '$.status') as status,
                GETDATE() as processed_at
            FROM bronze.bronze_orders
            WHERE order_id NOT IN (SELECT order_id FROM silver.silver_orders)
        """
        
        conn.execute_query(query)
        
        # Get count
        result = conn.execute_query("SELECT COUNT(*) as cnt FROM silver.silver_orders")
        count = result[0]['cnt']
    
    print(f"✅ Silver Layer Complete: {count} records")
    return count


def run_gold_layer():
    """Aggregate to Gold"""
    print("\n" + "="*70)
    print("🥇 GOLD LAYER - BUSINESS METRICS")
    print("="*70)
    
    db = get_database_connector()
    
    with db as conn:
        # Daily sales summary
        query = """
            MERGE gold.gold_sales_summary AS target
            USING (
                SELECT 
                    order_date as summary_date,
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_revenue,
                    COUNT(DISTINCT customer_id) as total_customers,
                    AVG(total_amount) as average_order_value,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as total_products_sold
                FROM silver.silver_orders
                GROUP BY order_date
            ) AS source
            ON target.summary_date = source.summary_date
            WHEN MATCHED THEN
                UPDATE SET 
                    total_orders = source.total_orders,
                    total_revenue = source.total_revenue,
                    total_customers = source.total_customers,
                    average_order_value = source.average_order_value,
                    total_products_sold = source.total_products_sold,
                    updated_at = GETDATE()
            WHEN NOT MATCHED THEN
                INSERT (summary_date, total_orders, total_revenue, total_customers, average_order_value, total_products_sold)
                VALUES (source.summary_date, source.total_orders, source.total_revenue, source.total_customers, source.average_order_value, source.total_products_sold);
        """
        
        conn.execute_query(query)
        
        # Get count
        result = conn.execute_query("SELECT COUNT(*) as cnt FROM gold.gold_sales_summary")
        count = result[0]['cnt']
    
    print(f"✅ Gold Layer Complete: {count} records")
    return count


def data_quality_check():
    """Run data quality checks"""
    print("\n" + "="*70)
    print("🔍 DATA QUALITY CHECKS")
    print("="*70)
    
    db = get_database_connector()
    
    with db as conn:
        # Check for data consistency
        result = conn.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM bronze.bronze_orders) as bronze_count,
                (SELECT COUNT(*) FROM silver.silver_orders) as silver_count,
                (SELECT COUNT(*) FROM gold.gold_sales_summary) as gold_count
        """)
        
        bronze = result[0]['bronze_count']
        silver = result[0]['silver_count']
        gold = result[0]['gold_count']
        
        print(f"   Bronze Records: {bronze}")
        print(f"   Silver Records: {silver}")
        print(f"   Gold Records: {gold}")
        
        # Validation
        if silver < bronze * 0.9:
            print("   ⚠️  WARNING: Significant data loss in Silver layer")
        else:
            print("   ✅ Data consistency validated")
    
    return True


def main():
    """Execute complete ETL pipeline"""
    print("\n" + "="*70)
    print("🚀 SALLA DATA WAREHOUSE - COMPLETE ETL PIPELINE")
    print(f"⏰ Started: {datetime.now()}")
    print("="*70)
    
    try:
        # Phase 1: Bronze
        bronze_count = run_bronze_layer()
        
        # Phase 2: Silver
        silver_count = run_silver_layer()
        
        # Phase 3: Gold
        gold_count = run_gold_layer()
        
        # Phase 4: Quality Check
        data_quality_check()
        
        # Summary
        print("\n" + "="*70)
        print("🎉 ETL PIPELINE COMPLETED SUCCESSFULLY")
        print("="*70)
        print(f"   Bronze: {bronze_count} records")
        print(f"   Silver: {silver_count} records")
        print(f"   Gold: {gold_count} records")
        print(f"⏰ Finished: {datetime.now()}")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ETL Pipeline Failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
