"""
Airflow DAG for Bronze Layer - Salla API Data Extraction

This DAG extracts raw data from Salla API and loads it into the Bronze layer.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.transformations.bronze_extractor import BronzeExtractor


# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}


def extract_orders(**context):
    """Extract orders from Salla API to Bronze layer."""
    extractor = BronzeExtractor()
    records_count = extractor.extract_orders()
    context['task_instance'].xcom_push(key='orders_count', value=records_count)
    return records_count


def extract_customers(**context):
    """Extract customers from Salla API to Bronze layer."""
    extractor = BronzeExtractor()
    records_count = extractor.extract_customers()
    context['task_instance'].xcom_push(key='customers_count', value=records_count)
    return records_count


def extract_products(**context):
    """Extract products from Salla API to Bronze layer."""
    extractor = BronzeExtractor()
    records_count = extractor.extract_products()
    context['task_instance'].xcom_push(key='products_count', value=records_count)
    return records_count


# Create DAG
with DAG(
    dag_id='salla_bronze_extraction',
    default_args=default_args,
    description='Extract raw data from Salla API to Bronze layer',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=days_ago(1),
    catchup=False,
    tags=['salla', 'bronze', 'extraction'],
) as dag:
    
    # Task 1: Extract Orders
    extract_orders_task = PythonOperator(
        task_id='extract_orders',
        python_callable=extract_orders,
        provide_context=True,
    )
    
    # Task 2: Extract Customers
    extract_customers_task = PythonOperator(
        task_id='extract_customers',
        python_callable=extract_customers,
        provide_context=True,
    )
    
    # Task 3: Extract Products
    extract_products_task = PythonOperator(
        task_id='extract_products',
        python_callable=extract_products,
        provide_context=True,
    )
    
    # Define task dependencies (all can run in parallel)
    [extract_orders_task, extract_customers_task, extract_products_task]
