"""
Data Validator using Great Expectations

Provides data validation framework for ensuring data quality.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

try:
    import great_expectations as gx
    from great_expectations.core.batch import RuntimeBatchRequest
    from great_expectations.checkpoint import SimpleCheckpoint
    HAS_GX = True
except ImportError:
    HAS_GX = False
    logging.warning("great_expectations not installed. Data validation features will be limited.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass


class DataValidator:
    """
    Data validation framework using Great Expectations.
    Provides schema validation, data quality checks, and metrics.
    """
    
    def __init__(self, context_root_dir: Optional[str] = None):
        """
        Initialize the data validator.
        
        Args:
            context_root_dir: Root directory for Great Expectations context
        """
        self.has_gx = HAS_GX
        self.context = None
        self.validation_results = []
        
        if self.has_gx:
            try:
                if context_root_dir:
                    self.context = gx.get_context(context_root_dir=context_root_dir)
                else:
                    # Create in-memory context
                    self.context = gx.get_context()
                logger.info("Great Expectations context initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize GX context: {str(e)}")
                self.has_gx = False
    
    def validate_schema(self, data: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against expected schema.
        
        Args:
            data: DataFrame to validate
            schema: Schema definition with expected columns and types
            
        Returns:
            Validation result dictionary
        """
        result = {
            'success': True,
            'errors': [],
            'warnings': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check if DataFrame is empty
            if data.empty:
                result['warnings'].append("DataFrame is empty")
                return result
            
            # Validate required columns
            required_columns = schema.get('required_fields', [])
            missing_columns = set(required_columns) - set(data.columns)
            
            if missing_columns:
                result['success'] = False
                result['errors'].append(f"Missing required columns: {list(missing_columns)}")
            
            # Validate data types
            expected_types = schema.get('field_types', {})
            for column, expected_type in expected_types.items():
                if column in data.columns:
                    actual_type = str(data[column].dtype)
                    if not self._types_compatible(actual_type, expected_type):
                        result['warnings'].append(
                            f"Column '{column}' type mismatch: expected {expected_type}, got {actual_type}"
                        )
            
            # Check for null values in non-nullable columns
            non_nullable = schema.get('non_nullable_fields', [])
            for column in non_nullable:
                if column in data.columns:
                    null_count = data[column].isnull().sum()
                    if null_count > 0:
                        result['errors'].append(
                            f"Column '{column}' has {null_count} null values but should not"
                        )
                        result['success'] = False
            
        except Exception as e:
            result['success'] = False
            result['errors'].append(f"Schema validation error: {str(e)}")
            logger.error(f"Schema validation failed: {str(e)}")
        
        return result
    
    def _types_compatible(self, actual: str, expected: str) -> bool:
        """
        Check if actual type is compatible with expected type.
        
        Args:
            actual: Actual data type
            expected: Expected data type
            
        Returns:
            True if compatible, False otherwise
        """
        # Normalize type names
        actual = actual.lower()
        expected = expected.lower()
        
        # Type compatibility mapping
        compatible_types = {
            'int': ['int', 'int64', 'int32', 'integer'],
            'float': ['float', 'float64', 'float32', 'double'],
            'string': ['str', 'string', 'object', 'text'],
            'bool': ['bool', 'boolean'],
            'datetime': ['datetime', 'datetime64', 'timestamp']
        }
        
        for base_type, variants in compatible_types.items():
            if expected in variants and actual in variants:
                return True
        
        return actual == expected
    
    def validate_data_quality(self, data: pd.DataFrame, 
                             expectations: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Validate data quality using custom expectations.
        
        Args:
            data: DataFrame to validate
            expectations: List of expectation configurations
            
        Returns:
            Validation result dictionary
        """
        result = {
            'success': True,
            'checks_passed': 0,
            'checks_failed': 0,
            'details': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if expectations is None:
                expectations = self._get_default_expectations()
            
            for expectation in expectations:
                check_result = self._run_quality_check(data, expectation)
                result['details'].append(check_result)
                
                if check_result['passed']:
                    result['checks_passed'] += 1
                else:
                    result['checks_failed'] += 1
                    result['success'] = False
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            logger.error(f"Data quality validation failed: {str(e)}")
        
        return result
    
    def _get_default_expectations(self) -> List[Dict]:
        """
        Get default data quality expectations.
        
        Returns:
            List of expectation configurations
        """
        return [
            {
                'name': 'no_duplicate_rows',
                'description': 'Check for duplicate rows'
            },
            {
                'name': 'no_null_values',
                'description': 'Check for null values in critical columns'
            }
        ]
    
    def _run_quality_check(self, data: pd.DataFrame, expectation: Dict) -> Dict[str, Any]:
        """
        Run a single data quality check.
        
        Args:
            data: DataFrame to check
            expectation: Expectation configuration
            
        Returns:
            Check result
        """
        check_name = expectation.get('name')
        result = {
            'check': check_name,
            'description': expectation.get('description', ''),
            'passed': True,
            'message': ''
        }
        
        try:
            if check_name == 'no_duplicate_rows':
                duplicates = data.duplicated().sum()
                result['passed'] = duplicates == 0
                result['message'] = f"Found {duplicates} duplicate rows"
                
            elif check_name == 'no_null_values':
                null_counts = data.isnull().sum()
                total_nulls = null_counts.sum()
                result['passed'] = total_nulls == 0
                result['message'] = f"Found {total_nulls} null values"
                
            else:
                result['message'] = f"Unknown check: {check_name}"
                
        except Exception as e:
            result['passed'] = False
            result['message'] = f"Check failed: {str(e)}"
        
        return result
    
    def validate_with_great_expectations(self, data: pd.DataFrame, 
                                        expectation_suite_name: str) -> Dict[str, Any]:
        """
        Validate data using Great Expectations if available.
        
        Args:
            data: DataFrame to validate
            expectation_suite_name: Name of the expectation suite
            
        Returns:
            Validation result dictionary
        """
        if not self.has_gx or not self.context:
            return {
                'success': False,
                'message': 'Great Expectations not available'
            }
        
        try:
            # Create a runtime batch request
            batch_request = RuntimeBatchRequest(
                datasource_name="runtime_datasource",
                data_connector_name="runtime_data_connector",
                data_asset_name="validation_data",
                runtime_parameters={"batch_data": data},
                batch_identifiers={"default_identifier_name": "default_identifier"}
            )
            
            # Get or create expectation suite
            try:
                expectation_suite = self.context.get_expectation_suite(expectation_suite_name)
            except:
                expectation_suite = self.context.create_expectation_suite(expectation_suite_name)
            
            # Validate
            validator = self.context.get_validator(
                batch_request=batch_request,
                expectation_suite=expectation_suite
            )
            
            validation_result = validator.validate()
            
            return {
                'success': validation_result.success,
                'statistics': validation_result.statistics,
                'results': validation_result.results
            }
            
        except Exception as e:
            logger.error(f"Great Expectations validation failed: {str(e)}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_data_profile(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate data profile with statistics and metrics.
        
        Args:
            data: DataFrame to profile
            
        Returns:
            Data profile dictionary
        """
        profile = {
            'row_count': len(data),
            'column_count': len(data.columns),
            'columns': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            for column in data.columns:
                col_profile = {
                    'type': str(data[column].dtype),
                    'null_count': int(data[column].isnull().sum()),
                    'null_percentage': float(data[column].isnull().sum() / len(data) * 100),
                    'unique_count': int(data[column].nunique())
                }
                
                # Add numeric statistics if applicable
                if pd.api.types.is_numeric_dtype(data[column]):
                    col_profile.update({
                        'mean': float(data[column].mean()) if not data[column].isnull().all() else None,
                        'std': float(data[column].std()) if not data[column].isnull().all() else None,
                        'min': float(data[column].min()) if not data[column].isnull().all() else None,
                        'max': float(data[column].max()) if not data[column].isnull().all() else None
                    })
                
                profile['columns'][column] = col_profile
                
        except Exception as e:
            logger.error(f"Error generating data profile: {str(e)}")
            profile['error'] = str(e)
        
        return profile
    
    def compare_schemas(self, schema1: Dict[str, Any], 
                       schema2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two schemas and identify differences.
        
        Args:
            schema1: First schema
            schema2: Second schema
            
        Returns:
            Comparison result
        """
        comparison = {
            'identical': True,
            'added_fields': [],
            'removed_fields': [],
            'type_changes': []
        }
        
        try:
            fields1 = set(schema1.get('required_fields', []))
            fields2 = set(schema2.get('required_fields', []))
            
            comparison['added_fields'] = list(fields2 - fields1)
            comparison['removed_fields'] = list(fields1 - fields2)
            
            # Compare types for common fields
            types1 = schema1.get('field_types', {})
            types2 = schema2.get('field_types', {})
            
            for field in fields1.intersection(fields2):
                if types1.get(field) != types2.get(field):
                    comparison['type_changes'].append({
                        'field': field,
                        'old_type': types1.get(field),
                        'new_type': types2.get(field)
                    })
            
            comparison['identical'] = not (
                comparison['added_fields'] or 
                comparison['removed_fields'] or 
                comparison['type_changes']
            )
            
        except Exception as e:
            logger.error(f"Schema comparison failed: {str(e)}")
            comparison['error'] = str(e)
        
        return comparison
