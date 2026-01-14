"""
Airflow DAG for Gold Layer - Dimensional Model Population

This DAG transforms data from Silver to Gold layer (dimensional model).
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

from src.transformations.gold_transformer import GoldTransformer


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


def load_dim_date(**context):
    """Load date dimension table."""
    transformer = GoldTransformer()
    records_count = transformer.load_dim_date()
    return records_count


def load_dim_customers(**context):
    """Load customers dimension table."""
    transformer = GoldTransformer()
    records_count = transformer.load_dim_customers()
    return records_count


def load_dim_products(**context):
    """Load products dimension table."""
    transformer = GoldTransformer()
    records_count = transformer.load_dim_products()
    return records_count


def load_dim_payment_methods(**context):
    """Load payment methods dimension table."""
    transformer = GoldTransformer()
    records_count = transformer.load_dim_payment_methods()
    return records_count


def load_dim_shipping_methods(**context):
    """Load shipping methods dimension table."""
    transformer = GoldTransformer()
    records_count = transformer.load_dim_shipping_methods()
    return records_count


def load_fact_orders(**context):
    """Load orders fact table."""
    transformer = GoldTransformer()
    records_count = transformer.load_fact_orders()
    return records_count


# Create DAG
with DAG(
    dag_id='salla_gold_dimensional',
    default_args=default_args,
    description='Transform data from Silver to Gold layer (dimensional model)',
    schedule_interval='0 4 * * *',  # Daily at 4 AM (1 hour after Silver)
    start_date=days_ago(1),
    catchup=False,
    tags=['salla', 'gold', 'dimensional'],
) as dag:
    
    # Wait for Silver transformation to complete
    wait_for_silver = ExternalTaskSensor(
        task_id='wait_for_silver_transformation',
        external_dag_id='salla_silver_transformation',
        external_task_id=None,  # Wait for entire DAG
        timeout=3600,  # 1 hour timeout
        allowed_states=['success'],
        failed_states=['failed', 'skipped'],
        mode='reschedule',
    )
    
    # Dimension loads
    dim_date_task = PythonOperator(
        task_id='load_dim_date',
        python_callable=load_dim_date,
        provide_context=True,
    )
    
    dim_customers_task = PythonOperator(
        task_id='load_dim_customers',
        python_callable=load_dim_customers,
        provide_context=True,
    )
    
    dim_products_task = PythonOperator(
        task_id='load_dim_products',
        python_callable=load_dim_products,
        provide_context=True,
    )
    
    dim_payment_task = PythonOperator(
        task_id='load_dim_payment_methods',
        python_callable=load_dim_payment_methods,
        provide_context=True,
    )
    
    dim_shipping_task = PythonOperator(
        task_id='load_dim_shipping_methods',
        python_callable=load_dim_shipping_methods,
        provide_context=True,
    )
    
    # Fact load
    fact_orders_task = PythonOperator(
        task_id='load_fact_orders',
        python_callable=load_fact_orders,
        provide_context=True,
    )
    
    # Define task dependencies
    # Wait for Silver, then load dimensions in parallel, then load fact
    wait_for_silver >> [dim_date_task, dim_customers_task, dim_products_task, 
                        dim_payment_task, dim_shipping_task]
    
    [dim_date_task, dim_customers_task, dim_products_task, 
     dim_payment_task, dim_shipping_task] >> fact_orders_task
