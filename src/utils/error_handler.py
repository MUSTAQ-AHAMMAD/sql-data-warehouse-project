"""
Error Handler with Dead Letter Queue (DLQ)

Centralized error handling, retry mechanisms, and failed record management.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from pathlib import Path
from enum import Enum
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"
    TRANSFORMATION_ERROR = "transformation_error"
    DATABASE_ERROR = "database_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorHandler:
    """
    Centralized error handler with DLQ support.
    Handles error logging, retry mechanisms, and failed record management.
    """
    
    def __init__(self, dlq_dir: Optional[str] = None, max_retries: int = 3):
        """
        Initialize the error handler.
        
        Args:
            dlq_dir: Directory for storing failed records (DLQ)
            max_retries: Maximum number of retry attempts
        """
        self.max_retries = max_retries
        self.dlq_dir = dlq_dir or os.path.join(
            os.path.dirname(__file__), '../../data/dlq'
        )
        self.error_log = []
        
        # Create DLQ directory if it doesn't exist
        Path(self.dlq_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Error handler initialized with DLQ at: {self.dlq_dir}")
    
    def handle_error(self, error: Exception, context: Dict[str, Any],
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR) -> Dict[str, Any]:
        """
        Handle an error with logging and classification.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            severity: Error severity level
            category: Error category
            
        Returns:
            Error record dictionary
        """
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'severity': severity.value,
            'category': category.value,
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        # Log error based on severity
        log_message = (
            f"[{severity.value.upper()}] {category.value}: {str(error)} | "
            f"Context: {context.get('operation', 'unknown')}"
        )
        
        if severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(log_message)
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Store in error log
        self.error_log.append(error_record)
        
        return error_record
    
    def send_to_dlq(self, record: Dict[str, Any], error: Exception,
                   source: str, entity_type: str) -> str:
        """
        Send a failed record to the Dead Letter Queue.
        
        Args:
            record: The failed record
            error: The error that caused the failure
            source: Data source name
            entity_type: Type of entity (orders, customers, etc.)
            
        Returns:
            Path to the DLQ file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        filename = f"{source}_{entity_type}_{timestamp}.json"
        filepath = os.path.join(self.dlq_dir, filename)
        
        dlq_record = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'entity_type': entity_type,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'record': record,
            'traceback': traceback.format_exc()
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(dlq_record, f, indent=2, default=str)
            
            logger.info(f"Record sent to DLQ: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to write to DLQ: {str(e)}")
            raise
    
    def retry_with_backoff(self, func: Callable, *args, 
                          max_retries: Optional[int] = None,
                          backoff_factor: float = 2.0,
                          **kwargs) -> Any:
        """
        Execute a function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            max_retries: Maximum number of retries (defaults to instance max_retries)
            backoff_factor: Multiplier for backoff delay
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        import time
        
        max_retries = max_retries or self.max_retries
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries:
                    delay = backoff_factor ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {max_retries + 1} attempts failed. Last error: {str(e)}"
                    )
        
        raise last_exception
    
    def process_with_error_handling(self, records: List[Dict], 
                                   process_func: Callable,
                                   source: str,
                                   entity_type: str,
                                   fail_fast: bool = False) -> Dict[str, Any]:
        """
        Process records with error handling and DLQ support.
        
        Args:
            records: List of records to process
            process_func: Function to process each record
            source: Data source name
            entity_type: Type of entity
            fail_fast: If True, stop on first error; if False, continue processing
            
        Returns:
            Processing result with success/failure counts
        """
        result = {
            'total': len(records),
            'successful': 0,
            'failed': 0,
            'errors': [],
            'dlq_files': []
        }
        
        for idx, record in enumerate(records):
            try:
                process_func(record)
                result['successful'] += 1
                
            except Exception as e:
                result['failed'] += 1
                
                # Log error
                error_record = self.handle_error(
                    e,
                    context={
                        'operation': 'record_processing',
                        'source': source,
                        'entity_type': entity_type,
                        'record_index': idx
                    },
                    severity=ErrorSeverity.MEDIUM,
                    category=self._categorize_error(e)
                )
                result['errors'].append(error_record)
                
                # Send to DLQ
                try:
                    dlq_file = self.send_to_dlq(record, e, source, entity_type)
                    result['dlq_files'].append(dlq_file)
                except Exception as dlq_error:
                    logger.error(f"Failed to send record to DLQ: {str(dlq_error)}")
                
                # Stop if fail_fast is enabled
                if fail_fast:
                    logger.error("Stopping processing due to error (fail_fast=True)")
                    break
        
        logger.info(
            f"Processing complete: {result['successful']} successful, "
            f"{result['failed']} failed out of {result['total']}"
        )
        
        return result
    
    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Categorize an error based on its type and message.
        
        Args:
            error: The exception to categorize
            
        Returns:
            Error category
        """
        error_type = type(error).__name__
        error_msg = str(error).lower()
        
        # API and network errors
        if 'connection' in error_msg or 'timeout' in error_msg or 'network' in error_msg:
            return ErrorCategory.NETWORK_ERROR
        
        # Authentication errors
        if 'auth' in error_msg or 'token' in error_msg or 'unauthorized' in error_msg:
            return ErrorCategory.AUTHENTICATION_ERROR
        
        # Validation errors
        if 'validation' in error_msg or 'schema' in error_msg or 'invalid' in error_msg:
            return ErrorCategory.VALIDATION_ERROR
        
        # Database errors
        if 'database' in error_msg or 'sql' in error_msg or 'connection' in error_msg:
            return ErrorCategory.DATABASE_ERROR
        
        # Transformation errors
        if 'transform' in error_msg or 'parse' in error_msg or 'convert' in error_msg:
            return ErrorCategory.TRANSFORMATION_ERROR
        
        return ErrorCategory.UNKNOWN_ERROR
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of all errors encountered.
        
        Returns:
            Error summary dictionary
        """
        summary = {
            'total_errors': len(self.error_log),
            'by_severity': {},
            'by_category': {},
            'recent_errors': self.error_log[-10:] if self.error_log else []
        }
        
        # Count by severity
        for severity in ErrorSeverity:
            count = sum(1 for e in self.error_log if e['severity'] == severity.value)
            summary['by_severity'][severity.value] = count
        
        # Count by category
        for category in ErrorCategory:
            count = sum(1 for e in self.error_log if e['category'] == category.value)
            summary['by_category'][category.value] = count
        
        return summary
    
    def get_dlq_files(self, source: Optional[str] = None,
                     entity_type: Optional[str] = None) -> List[str]:
        """
        Get list of DLQ files with optional filtering.
        
        Args:
            source: Filter by data source
            entity_type: Filter by entity type
            
        Returns:
            List of DLQ file paths
        """
        dlq_files = []
        
        try:
            for filename in os.listdir(self.dlq_dir):
                if not filename.endswith('.json'):
                    continue
                
                # Apply filters
                if source and not filename.startswith(source):
                    continue
                
                if entity_type and entity_type not in filename:
                    continue
                
                dlq_files.append(os.path.join(self.dlq_dir, filename))
                
        except Exception as e:
            logger.error(f"Failed to list DLQ files: {str(e)}")
        
        return dlq_files
    
    def retry_dlq_records(self, process_func: Callable, 
                         source: Optional[str] = None,
                         entity_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Retry processing failed records from DLQ.
        
        Args:
            process_func: Function to process records
            source: Filter by data source
            entity_type: Filter by entity type
            
        Returns:
            Retry result dictionary
        """
        result = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'removed_files': []
        }
        
        dlq_files = self.get_dlq_files(source, entity_type)
        result['total'] = len(dlq_files)
        
        for filepath in dlq_files:
            try:
                # Load DLQ record
                with open(filepath, 'r') as f:
                    dlq_record = json.load(f)
                
                record = dlq_record.get('record', {})
                
                # Retry processing
                process_func(record)
                
                # Remove from DLQ on success
                os.remove(filepath)
                result['successful'] += 1
                result['removed_files'].append(filepath)
                logger.info(f"Successfully reprocessed and removed: {filepath}")
                
            except Exception as e:
                result['failed'] += 1
                logger.error(f"Failed to reprocess {filepath}: {str(e)}")
        
        return result
    
    def clear_error_log(self):
        """Clear the in-memory error log"""
        self.error_log.clear()
        logger.info("Error log cleared")
    
    def export_error_log(self, filepath: str):
        """
        Export error log to a file.
        
        Args:
            filepath: Path to export file
        """
        try:
            with open(filepath, 'w') as f:
                json.dump(self.error_log, f, indent=2, default=str)
            logger.info(f"Error log exported to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to export error log: {str(e)}")
            raise
