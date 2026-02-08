"""
Salla Data Warehouse ETL Pipeline
Production-grade DAG for Docker environment
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
import sys
import os

# Add project root to path
project_root = '/opt/airflow'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1),
}

def extract_bronze():
    """Extract data from Salla API to Bronze layer"""
    print("🥉 Extracting to Bronze layer...")
    os.chdir(project_root)
    from src.transformations.bronze_extractor import main as bronze_main
    bronze_main()
    print("✅ Bronze extraction completed")

def transform_silver():
    """Transform Bronze data to Silver layer"""
    print("🥈 Transforming to Silver layer...")
    os.chdir(project_root)
    from src.transformations.silver_transformer import main as silver_main
    silver_main()
    print("✅ Silver transformation completed")

def aggregate_gold():
    """Aggregate Silver data to Gold layer"""
    print("🥇 Aggregating to Gold layer...")
    os.chdir(project_root)
    from src.transformations.gold_transformer import main as gold_main
    gold_main()
    print("✅ Gold aggregation completed")

def data_quality_check():
    """Verify data quality in all layers"""
    print("🔍 Running data quality checks...")
    os.chdir(project_root)
    from src.database.sqlserver_connector import SQLServerConnector
    
    with SQLServerConnector() as db:
        result = db.execute_query("""
            SELECT 
                (SELECT COUNT(*) FROM bronze.bronze_orders) as bronze_orders,
                (SELECT COUNT(*) FROM silver.silver_orders) as silver_orders,
                (SELECT COUNT(*) FROM gold.gold_sales_summary) as gold_summary
        """)
        
        print(f"📊 Bronze Orders: {result[0]['bronze_orders']}")
        print(f"📊 Silver Orders: {result[0]['silver_orders']}")
        print(f"📊 Gold Summary: {result[0]['gold_summary']}")
        
        # Quality checks
        if result[0]['bronze_orders'] == 0:
            raise ValueError("No data in Bronze layer!")
        if result[0]['silver_orders'] < result[0]['bronze_orders'] * 0.9:
            raise ValueError("Data loss detected in Silver transformation!")
        
        print("✅ Data quality check passed")

with DAG(
    'salla_etl_pipeline',
    default_args=default_args,
    description='Production ETL pipeline for Salla data warehouse',
    schedule='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    max_active_runs=1,
    tags=['production', 'etl', 'salla', 'data-warehouse'],
) as dag:
    
    # ETL Tasks
    with TaskGroup('bronze_layer') as bronze_layer:
        extract = PythonOperator(
            task_id='extract_data',
            python_callable=extract_bronze,
        )
    
    with TaskGroup('silver_layer') as silver_layer:
        transform = PythonOperator(
            task_id='transform_data',
            python_callable=transform_silver,
        )
    
    with TaskGroup('gold_layer') as gold_layer:
        aggregate = PythonOperator(
            task_id='aggregate_data',
            python_callable=aggregate_gold,
        )
    
    quality_check = PythonOperator(
        task_id='data_quality_check',
        python_callable=data_quality_check,
    )
    
    # Define pipeline flow
    bronze_layer >> silver_layer >> gold_layer >> quality_check
