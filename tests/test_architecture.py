#!/usr/bin/env python3
"""
Test script for validating the enhanced ETL architecture components.
"""

import os
import sys
import yaml
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.data_source_registry import get_registry
from src.api.salla_adapter import SallaAPIAdapter
from src.utils.data_validator import DataValidator
from src.utils.error_handler import ErrorHandler, ErrorSeverity, ErrorCategory


def test_data_source_registry():
    """Test data source registry functionality"""
    print("\n" + "="*60)
    print("Testing Data Source Registry")
    print("="*60)
    
    try:
        # Get registry instance
        registry = get_registry()
        print("✓ Registry instance created")
        
        # Register Salla adapter
        registry.register_adapter('salla', SallaAPIAdapter)
        print("✓ Salla adapter registered")
        
        # List sources
        sources = registry.list_sources()
        print(f"✓ Registered sources: {sources}")
        
        # List configured sources
        configured = registry.list_configured_sources()
        print(f"✓ Configured sources: {configured}")
        
        # Validate configuration
        validation = registry.validate_configuration()
        print(f"✓ Configuration validation:")
        print(f"  - Valid: {validation['valid']}")
        print(f"  - Invalid: {validation['invalid']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Registry test failed: {str(e)}")
        return False


def test_data_validator():
    """Test data validator functionality"""
    print("\n" + "="*60)
    print("Testing Data Validator")
    print("="*60)
    
    try:
        # Create validator instance
        validator = DataValidator()
        print("✓ Validator instance created")
        
        # Create sample data
        sample_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Product A', 'Product B', 'Product C'],
            'price': [10.99, 20.99, 30.99],
            'stock': [100, 50, 25]
        })
        print("✓ Sample data created")
        
        # Define schema
        schema = {
            'required_fields': ['id', 'name', 'price'],
            'field_types': {
                'id': 'int',
                'name': 'string',
                'price': 'float',
                'stock': 'int'
            },
            'non_nullable_fields': ['id', 'name']
        }
        
        # Validate schema
        result = validator.validate_schema(sample_data, schema)
        print(f"✓ Schema validation: {'Passed' if result['success'] else 'Failed'}")
        if result['errors']:
            print(f"  - Errors: {result['errors']}")
        if result['warnings']:
            print(f"  - Warnings: {result['warnings']}")
        
        # Validate data quality
        quality_result = validator.validate_data_quality(sample_data)
        print(f"✓ Quality validation: {quality_result['checks_passed']}/{quality_result['checks_passed'] + quality_result['checks_failed']} passed")
        
        # Get data profile
        profile = validator.get_data_profile(sample_data)
        print(f"✓ Data profile generated:")
        print(f"  - Rows: {profile['row_count']}")
        print(f"  - Columns: {profile['column_count']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Validator test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handler():
    """Test error handler functionality"""
    print("\n" + "="*60)
    print("Testing Error Handler")
    print("="*60)
    
    try:
        # Create error handler instance
        error_handler = ErrorHandler()
        print("✓ Error handler instance created")
        print(f"  - DLQ directory: {error_handler.dlq_dir}")
        
        # Test error handling
        test_error = ValueError("Test error for demonstration")
        error_record = error_handler.handle_error(
            test_error,
            context={'operation': 'test_operation', 'source': 'test'},
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION_ERROR
        )
        print("✓ Error logged successfully")
        
        # Test DLQ
        test_record = {'id': 1, 'name': 'Test Record'}
        dlq_file = error_handler.send_to_dlq(
            test_record,
            test_error,
            source='test',
            entity_type='test_entity'
        )
        print(f"✓ Record sent to DLQ: {dlq_file}")
        
        # Get error summary
        summary = error_handler.get_error_summary()
        print(f"✓ Error summary generated:")
        print(f"  - Total errors: {summary['total_errors']}")
        
        # Get DLQ files
        dlq_files = error_handler.get_dlq_files()
        print(f"✓ DLQ files count: {len(dlq_files)}")
        
        # Clean up test DLQ file
        if os.path.exists(dlq_file):
            os.remove(dlq_file)
            print("✓ Test DLQ file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handler test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_generic_adapter():
    """Test generic API adapter interface"""
    print("\n" + "="*60)
    print("Testing Generic API Adapter")
    print("="*60)
    
    try:
        # Test schema retrieval
        config = {
            'api_token': 'test_token',
            'base_url': 'https://api.example.com',
            'batch_size': 100,
            'source_name': 'test'
        }
        
        adapter = SallaAPIAdapter(config)
        print("✓ Salla adapter instance created")
        
        # Get schema
        schema = adapter.get_schema('orders')
        print(f"✓ Schema retrieved for 'orders':")
        print(f"  - Required fields: {schema.get('required_fields', [])}")
        
        # Get supported entities
        entities = adapter.get_supported_entities()
        print(f"✓ Supported entities: {entities}")
        
        return True
        
    except Exception as e:
        print(f"✗ Adapter test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ETL PIPELINE ARCHITECTURE - COMPONENT TESTS")
    print("="*60)
    print(f"Test started at: {datetime.now().isoformat()}")
    
    results = {
        'Data Source Registry': test_data_source_registry(),
        'Data Validator': test_data_validator(),
        'Error Handler': test_error_handler(),
        'Generic API Adapter': test_generic_adapter()
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(results.values())


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
