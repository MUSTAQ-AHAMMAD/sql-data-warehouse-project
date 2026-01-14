"""
Airflow DAG for Silver Layer - Data Transformation and Cleansing

This DAG transforms and cleanses data from Bronze to Silver layer.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.utils.dates import days_ago
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.transformations.silver_transformer import SilverTransformer


# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=3),
    'execution_timeout': timedelta(hours=1),
}


def transform_orders(**context):
    """Transform orders from Bronze to Silver layer."""
    transformer = SilverTransformer()
    records_count = transformer.transform_orders()
    context['task_instance'].xcom_push(key='orders_count', value=records_count)
    return records_count


def transform_customers(**context):
    """Transform customers from Bronze to Silver layer."""
    transformer = SilverTransformer()
    records_count = transformer.transform_customers()
    context['task_instance'].xcom_push(key='customers_count', value=records_count)
    return records_count


def transform_products(**context):
    """Transform products from Bronze to Silver layer."""
    transformer = SilverTransformer()
    records_count = transformer.transform_products()
    context['task_instance'].xcom_push(key='products_count', value=records_count)
    return records_count


# Create DAG
with DAG(
    dag_id='salla_silver_transformation',
    default_args=default_args,
    description='Transform and cleanse data from Bronze to Silver layer',
    schedule_interval='0 3 * * *',  # Daily at 3 AM (1 hour after Bronze)
    start_date=days_ago(1),
    catchup=False,
    tags=['salla', 'silver', 'transformation'],
) as dag:
    
    # Wait for Bronze extraction to complete
    wait_for_bronze = ExternalTaskSensor(
        task_id='wait_for_bronze_extraction',
        external_dag_id='salla_bronze_extraction',
        external_task_id=None,  # Wait for entire DAG
        timeout=3600,  # 1 hour timeout
        allowed_states=['success'],
        failed_states=['failed', 'skipped'],
        mode='reschedule',
    )
    
    # Task 1: Transform Orders
    transform_orders_task = PythonOperator(
        task_id='transform_orders',
        python_callable=transform_orders,
        provide_context=True,
    )
    
    # Task 2: Transform Customers
    transform_customers_task = PythonOperator(
        task_id='transform_customers',
        python_callable=transform_customers,
        provide_context=True,
    )
    
    # Task 3: Transform Products
    transform_products_task = PythonOperator(
        task_id='transform_products',
        python_callable=transform_products,
        provide_context=True,
    )
    
    # Define task dependencies
    wait_for_bronze >> [transform_orders_task, transform_customers_task, transform_products_task]
