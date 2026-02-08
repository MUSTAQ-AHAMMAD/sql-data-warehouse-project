"""
Salla Data Warehouse ETL Pipeline
Simple single DAG for complete ETL process
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Add project root
project_root = 'C:\\xampp\\htdocs\\sql-data-warehouse-project'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def extract_bronze():
    """Extract to Bronze layer"""
    print("Extracting to Bronze layer...")
    os.chdir(project_root)
    try:
        from src.transformations.bronze_extractor import main
        main()
        print("Bronze extraction completed")
    except Exception as e:
        print(f"Bronze extraction error: {e}")
        raise

def transform_silver():
    """Transform to Silver layer"""
    print("Transforming to Silver layer...")
    os.chdir(project_root)
    try:
        from src.transformations.silver_transformer import main
        main()
        print("Silver transformation completed")
    except Exception as e:
        print(f"Silver transformation error: {e}")
        raise

def aggregate_gold():
    """Aggregate to Gold layer"""
    print("Aggregating to Gold layer...")
    os.chdir(project_root)
    try:
        from src.transformations.gold_transformer import main
        main()
        print("Gold aggregation completed")
    except Exception as e:
        print(f"Gold aggregation error: {e}")
        raise

with DAG(
    'salla_etl_pipeline',
    default_args=default_args,
    description='Salla ETL Pipeline',
    schedule_interval='@daily',
    catchup=False,
    tags=['etl', 'salla'],
) as dag:
    
    extract = PythonOperator(
        task_id='extract_bronze',
        python_callable=extract_bronze,
    )
    
    transform = PythonOperator(
        task_id='transform_silver',
        python_callable=transform_silver,
    )
    
    aggregate = PythonOperator(
        task_id='aggregate_gold',
        python_callable=aggregate_gold,
    )
    
    extract >> transform >> aggregate
