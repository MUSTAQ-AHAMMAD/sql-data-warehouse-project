"""
API Testing Dashboard - Flask Application

Provides a web interface for testing API endpoints, viewing responses,
monitoring data quality, and validating transformations.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import pandas as pd

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.data_source_registry import get_registry
from src.api.salla_connector import SallaAPIConnector
from src.utils.data_validator import DataValidator
from src.utils.error_handler import ErrorHandler

load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
           static_folder='static',
           template_folder='templates')
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
registry = get_registry()
validator = DataValidator()
error_handler = ErrorHandler()

# Dashboard configuration
DASHBOARD_HOST = os.getenv('DASHBOARD_HOST', '0.0.0.0')
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 5000))
DASHBOARD_DEBUG = os.getenv('DASHBOARD_DEBUG', 'False').lower() == 'true'


@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/api/sources')
def list_sources():
    """List all registered data sources"""
    try:
        sources = registry.list_configured_sources()
        source_info = []
        
        for source in sources:
            config = registry.get_source_config(source)
            source_info.append({
                'name': source,
                'enabled': config.get('enabled', False),
                'description': config.get('description', ''),
                'supported_entities': config.get('supported_entities', [])
            })
        
        return jsonify({
            'success': True,
            'sources': source_info
        })
        
    except Exception as e:
        logger.error(f"Failed to list sources: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sources/<source_name>/test')
def test_source(source_name):
    """Test connection to a specific data source"""
    try:
        result = registry.test_connection(source_name)
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Failed to test source {source_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sources/<source_name>/entities/<entity_type>/fetch')
def fetch_data(source_name, entity_type):
    """Fetch data from a specific source and entity"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # For Salla, use the existing connector
        if source_name == 'salla':
            connector = SallaAPIConnector()
            
            if entity_type == 'orders':
                response = connector.fetch_orders(page=page, per_page=per_page)
            elif entity_type == 'customers':
                response = connector.fetch_customers(page=page, per_page=per_page)
            elif entity_type == 'products':
                response = connector.fetch_products(page=page, per_page=per_page)
            else:
                return jsonify({
                    'success': False,
                    'error': f'Unsupported entity type: {entity_type}'
                }), 400
            
            return jsonify({
                'success': True,
                'data': response
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Source {source_name} not yet implemented'
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to fetch data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/validate/schema', methods=['POST'])
def validate_schema():
    """Validate data against schema"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        entity_type = data.get('entity_type', 'orders')
        
        if not records:
            return jsonify({
                'success': False,
                'error': 'No records provided'
            }), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Load schema from config
        import yaml
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config/data_sources.yaml'
        )
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        schema = config.get('schemas', {}).get(entity_type, {})
        
        # Validate
        validation_result = validator.validate_schema(df, schema)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        logger.error(f"Schema validation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/validate/quality', methods=['POST'])
def validate_quality():
    """Validate data quality"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        
        if not records:
            return jsonify({
                'success': False,
                'error': 'No records provided'
            }), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Validate data quality
        quality_result = validator.validate_data_quality(df)
        
        # Get data profile
        profile = validator.get_data_profile(df)
        
        return jsonify({
            'success': True,
            'quality': quality_result,
            'profile': profile
        })
        
    except Exception as e:
        logger.error(f"Quality validation failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/errors/summary')
def error_summary():
    """Get error summary"""
    try:
        summary = error_handler.get_error_summary()
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Failed to get error summary: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/dlq/files')
def list_dlq_files():
    """List Dead Letter Queue files"""
    try:
        source = request.args.get('source')
        entity_type = request.args.get('entity_type')
        
        files = error_handler.get_dlq_files(source, entity_type)
        
        # Get file info
        file_info = []
        for filepath in files:
            try:
                with open(filepath, 'r') as f:
                    record = json.load(f)
                
                file_info.append({
                    'filename': os.path.basename(filepath),
                    'timestamp': record.get('timestamp'),
                    'source': record.get('source'),
                    'entity_type': record.get('entity_type'),
                    'error_type': record.get('error_type')
                })
            except:
                pass
        
        return jsonify({
            'success': True,
            'files': file_info,
            'count': len(file_info)
        })
        
    except Exception as e:
        logger.error(f"Failed to list DLQ files: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics"""
    try:
        # Count DLQ files
        dlq_files = error_handler.get_dlq_files()
        
        # Error summary
        error_summary_data = error_handler.get_error_summary()
        
        # Data sources
        sources = registry.list_configured_sources()
        
        stats = {
            'total_sources': len(sources),
            'total_errors': error_summary_data['total_errors'],
            'dlq_count': len(dlq_files),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    logger.info(f"Starting API Testing Dashboard on {DASHBOARD_HOST}:{DASHBOARD_PORT}")
    logger.info(f"Debug mode: {DASHBOARD_DEBUG}")
    
    # Register Salla adapter (example)
    try:
        from src.api.salla_connector import SallaAPIConnector
        # Note: SallaAPIConnector would need to inherit from GenericAPIAdapter
        # This is a placeholder - actual implementation would require refactoring
        logger.info("Salla connector available")
    except Exception as e:
        logger.warning(f"Could not load Salla connector: {str(e)}")
    
    app.run(
        host=DASHBOARD_HOST,
        port=DASHBOARD_PORT,
        debug=DASHBOARD_DEBUG
    )
