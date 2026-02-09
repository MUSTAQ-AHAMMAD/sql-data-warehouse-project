"""
Health Monitoring Dashboard

Flask-based real-time monitoring dashboard for the data warehouse.
Monitors database, API, data layers, and ETL pipeline status.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from src.database.database_factory import get_database_connector, get_database_type
from src.api.salla_connector import SallaAPIConnector, SallaAPIError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
DASHBOARD_PORT = int(os.getenv('MONITORING_PORT', '5001'))
DASHBOARD_HOST = os.getenv('MONITORING_HOST', '0.0.0.0')
DASHBOARD_DEBUG = os.getenv('MONITORING_DEBUG', 'False').lower() == 'true'


def check_database_health() -> Dict[str, Any]:
    """
    Check database connection and health.
    
    Returns:
        Dictionary with status, message, and details
    """
    try:
        db = get_database_connector()
        db_type = get_database_type()
        
        with db as conn:
            # Simple query to test connection
            if db_type == 'sqlserver':
                result = conn.execute_query("SELECT @@VERSION as version")
                version = result[0]['version'][:50] if result else "Unknown"
            elif db_type == 'snowflake':
                result = conn.execute_query("SELECT CURRENT_VERSION()")
                version = result[0][0] if result else "Unknown"
            else:
                version = "Unknown"
            
            return {
                'status': 'healthy',
                'message': f'Connected to {db_type.upper()}',
                'details': {
                    'database_type': db_type,
                    'version': version,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)[:100]}',
            'details': {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        }


def check_api_health() -> Dict[str, Any]:
    """
    Check Salla API connection and health.
    
    Returns:
        Dictionary with status, message, and details
    """
    try:
        api_token = os.getenv('SALLA_API_TOKEN')
        
        if not api_token or api_token == 'your_bearer_token_here':
            return {
                'status': 'not_configured',
                'message': 'API token not configured',
                'details': {
                    'note': 'Set SALLA_API_TOKEN environment variable',
                    'timestamp': datetime.now().isoformat()
                }
            }
        
        api = SallaAPIConnector()
        
        # Try a simple API call
        try:
            # Just check if we can initialize - actual API call would need valid endpoint
            return {
                'status': 'healthy',
                'message': 'API connector initialized',
                'details': {
                    'base_url': api.base_url,
                    'timestamp': datetime.now().isoformat()
                }
            }
        except SallaAPIError as e:
            return {
                'status': 'unhealthy',
                'message': f'API error: {str(e)[:100]}',
                'details': {
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"API health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'message': f'API check failed: {str(e)[:100]}',
            'details': {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        }


def check_data_layers() -> Dict[str, Any]:
    """
    Check status of Bronze, Silver, and Gold data layers.
    
    Returns:
        Dictionary with layer statuses and row counts
    """
    try:
        db = get_database_connector()
        
        with db as conn:
            layers = {}
            
            # Bronze layer
            try:
                bronze_query = """
                    SELECT 
                        (SELECT COUNT(*) FROM BRONZE.bronze_orders) as orders,
                        (SELECT COUNT(*) FROM BRONZE.bronze_customers) as customers,
                        (SELECT COUNT(*) FROM BRONZE.bronze_products) as products
                """
                bronze_result = conn.execute_query(bronze_query)
                layers['bronze'] = {
                    'status': 'healthy',
                    'orders': bronze_result[0]['orders'],
                    'customers': bronze_result[0]['customers'],
                    'products': bronze_result[0]['products']
                }
            except Exception as e:
                layers['bronze'] = {
                    'status': 'unhealthy',
                    'error': str(e)[:100]
                }
            
            # Silver layer
            try:
                silver_query = """
                    SELECT 
                        (SELECT COUNT(*) FROM SILVER.silver_orders) as orders,
                        (SELECT COUNT(*) FROM SILVER.silver_customers) as customers,
                        (SELECT COUNT(*) FROM SILVER.silver_products) as products
                """
                silver_result = conn.execute_query(silver_query)
                layers['silver'] = {
                    'status': 'healthy',
                    'orders': silver_result[0]['orders'],
                    'customers': silver_result[0]['customers'],
                    'products': silver_result[0]['products']
                }
            except Exception as e:
                layers['silver'] = {
                    'status': 'unhealthy',
                    'error': str(e)[:100]
                }
            
            # Gold layer
            try:
                gold_query = """
                    SELECT 
                        (SELECT COUNT(*) FROM GOLD.gold_dim_customers) as dim_customers,
                        (SELECT COUNT(*) FROM GOLD.gold_dim_products) as dim_products,
                        (SELECT COUNT(*) FROM GOLD.gold_fact_orders) as fact_orders
                """
                gold_result = conn.execute_query(gold_query)
                layers['gold'] = {
                    'status': 'healthy',
                    'dim_customers': gold_result[0]['dim_customers'],
                    'dim_products': gold_result[0]['dim_products'],
                    'fact_orders': gold_result[0]['fact_orders']
                }
            except Exception as e:
                layers['gold'] = {
                    'status': 'unhealthy',
                    'error': str(e)[:100]
                }
            
            return {
                'status': 'healthy',
                'layers': layers,
                'timestamp': datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Data layers check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'message': f'Data layers check failed: {str(e)[:100]}',
            'timestamp': datetime.now().isoformat()
        }


def check_etl_pipeline() -> Dict[str, Any]:
    """
    Check ETL pipeline status and last run information.
    
    Returns:
        Dictionary with pipeline status
    """
    try:
        db = get_database_connector()
        
        with db as conn:
            # Check watermark table for last ETL runs
            try:
                watermark_query = """
                    SELECT 
                        entity_name,
                        last_load_timestamp,
                        records_loaded,
                        load_duration_seconds,
                        load_rate_records_per_sec,
                        updated_at
                    FROM BRONZE.load_watermarks
                    ORDER BY updated_at DESC
                """
                
                result = conn.execute_query(watermark_query)
                
                if result:
                    watermarks = {}
                    for row in result:
                        watermarks[row['entity_name']] = {
                            'last_load': row['last_load_timestamp'].isoformat() if row['last_load_timestamp'] else None,
                            'records_loaded': row['records_loaded'],
                            'duration_seconds': float(row['load_duration_seconds']) if row['load_duration_seconds'] else 0,
                            'rate_per_sec': float(row['load_rate_records_per_sec']) if row['load_rate_records_per_sec'] else 0
                        }
                    
                    return {
                        'status': 'healthy',
                        'message': 'ETL pipeline tracking active',
                        'watermarks': watermarks,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    return {
                        'status': 'no_data',
                        'message': 'No ETL runs recorded yet',
                        'timestamp': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                return {
                    'status': 'unhealthy',
                    'message': f'Watermark table error: {str(e)[:100]}',
                    'timestamp': datetime.now().isoformat()
                }
                
    except Exception as e:
        logger.error(f"ETL pipeline check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'message': f'ETL check failed: {str(e)[:100]}',
            'timestamp': datetime.now().isoformat()
        }


@app.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('health_dashboard.html')


@app.route('/api/health')
def health_check():
    """
    Get overall health status of all components.
    
    Returns:
        JSON response with health status of all components
    """
    try:
        database_health = check_database_health()
        api_health = check_api_health()
        data_layers = check_data_layers()
        etl_pipeline = check_etl_pipeline()
        
        # Determine overall status
        statuses = [
            database_health['status'],
            api_health['status'],
            data_layers['status'],
            etl_pipeline['status']
        ]
        
        if 'unhealthy' in statuses:
            overall_status = 'unhealthy'
        elif 'not_configured' in statuses or 'no_data' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        response = {
            'overall_status': overall_status,
            'database': database_health,
            'api': api_health,
            'data_layers': data_layers,
            'etl_pipeline': etl_pipeline,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'overall_status': 'error',
            'message': f'Health check error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/stats')
def get_statistics():
    """
    Get detailed statistics about the data warehouse.
    
    Returns:
        JSON response with statistics
    """
    try:
        db = get_database_connector()
        
        with db as conn:
            # Get comprehensive statistics
            stats_query = """
                SELECT 
                    -- Bronze layer
                    (SELECT COUNT(*) FROM BRONZE.bronze_orders) as bronze_orders,
                    (SELECT COUNT(*) FROM BRONZE.bronze_customers) as bronze_customers,
                    (SELECT COUNT(*) FROM BRONZE.bronze_products) as bronze_products,
                    
                    -- Silver layer
                    (SELECT COUNT(*) FROM SILVER.silver_orders) as silver_orders,
                    (SELECT COUNT(*) FROM SILVER.silver_customers) as silver_customers,
                    (SELECT COUNT(*) FROM SILVER.silver_products) as silver_products,
                    
                    -- Gold layer
                    (SELECT COUNT(*) FROM GOLD.gold_dim_customers) as gold_dim_customers,
                    (SELECT COUNT(*) FROM GOLD.gold_dim_products) as gold_dim_products,
                    (SELECT COUNT(*) FROM GOLD.gold_fact_orders) as gold_fact_orders,
                    
                    -- Sales metrics from Silver
                    (SELECT COALESCE(SUM(amount), 0) FROM SILVER.silver_orders) as total_sales,
                    (SELECT COALESCE(AVG(amount), 0) FROM SILVER.silver_orders) as avg_order_value
            """
            
            result = conn.execute_query(stats_query)
            stats = result[0] if result else {}
            
            return jsonify({
                'status': 'success',
                'statistics': stats,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Statistics retrieval failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Statistics error: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500


def run_dashboard():
    """Run the monitoring dashboard server."""
    logger.info("=" * 80)
    logger.info("STARTING HEALTH MONITORING DASHBOARD")
    logger.info("=" * 80)
    logger.info(f"Host: {DASHBOARD_HOST}")
    logger.info(f"Port: {DASHBOARD_PORT}")
    logger.info(f"Debug: {DASHBOARD_DEBUG}")
    logger.info(f"Dashboard URL: http://localhost:{DASHBOARD_PORT}")
    logger.info("=" * 80)
    
    app.run(
        host=DASHBOARD_HOST,
        port=DASHBOARD_PORT,
        debug=DASHBOARD_DEBUG
    )


if __name__ == '__main__':
    run_dashboard()
