"""
Data Source Registry

Manages registration and configuration of multiple data sources.
Provides a centralized registry for all API adapters.
"""

import os
import yaml
import logging
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
from dotenv import load_dotenv

from .generic_api_adapter import GenericAPIAdapter

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSourceRegistry:
    """
    Registry for managing multiple data source adapters.
    Supports config-driven source registration and adapter instantiation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the data source registry.
        
        Args:
            config_path: Path to configuration file (YAML)
        """
        self._adapters: Dict[str, Type[GenericAPIAdapter]] = {}
        self._instances: Dict[str, GenericAPIAdapter] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}
        
        if config_path:
            self.load_config(config_path)
        else:
            # Try to load default config
            default_config = os.path.join(
                os.path.dirname(__file__), '../../config/data_sources.yaml'
            )
            if os.path.exists(default_config):
                self.load_config(default_config)
    
    def register_adapter(self, source_name: str, adapter_class: Type[GenericAPIAdapter]):
        """
        Register an adapter class for a data source.
        
        Args:
            source_name: Unique identifier for the data source
            adapter_class: Adapter class (must inherit from GenericAPIAdapter)
        """
        if not issubclass(adapter_class, GenericAPIAdapter):
            raise ValueError(
                f"Adapter class must inherit from GenericAPIAdapter, "
                f"got {adapter_class.__name__}"
            )
        
        self._adapters[source_name] = adapter_class
        logger.info(f"Registered adapter for data source: {source_name}")
    
    def load_config(self, config_path: str):
        """
        Load data source configurations from YAML file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data or 'data_sources' not in config_data:
                logger.warning(f"No data sources found in config: {config_path}")
                return
            
            for source_name, source_config in config_data['data_sources'].items():
                # Replace environment variable placeholders
                resolved_config = self._resolve_env_vars(source_config)
                self._configs[source_name] = resolved_config
                logger.info(f"Loaded configuration for data source: {source_name}")
                
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {str(e)}")
            raise
    
    def _resolve_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve environment variable references in configuration.
        
        Args:
            config: Configuration dictionary with potential ${ENV_VAR} placeholders
            
        Returns:
            Configuration with resolved environment variables
        """
        resolved = {}
        for key, value in config.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Extract environment variable name
                env_var = value[2:-1]
                resolved[key] = os.getenv(env_var, value)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_env_vars(value)
            else:
                resolved[key] = value
        return resolved
    
    def get_adapter(self, source_name: str, config: Optional[Dict[str, Any]] = None) -> GenericAPIAdapter:
        """
        Get or create an adapter instance for a data source.
        
        Args:
            source_name: Name of the data source
            config: Optional configuration override
            
        Returns:
            Adapter instance for the data source
            
        Raises:
            ValueError: If source is not registered or configured
        """
        # Return cached instance if exists
        if source_name in self._instances:
            return self._instances[source_name]
        
        # Check if adapter class is registered
        if source_name not in self._adapters:
            raise ValueError(
                f"No adapter registered for data source: {source_name}. "
                f"Available sources: {list(self._adapters.keys())}"
            )
        
        # Get configuration
        adapter_config = config or self._configs.get(source_name)
        if not adapter_config:
            raise ValueError(
                f"No configuration found for data source: {source_name}"
            )
        
        # Add source name to config
        adapter_config['source_name'] = source_name
        
        # Create adapter instance
        adapter_class = self._adapters[source_name]
        adapter_instance = adapter_class(adapter_config)
        
        # Cache the instance
        self._instances[source_name] = adapter_instance
        logger.info(f"Created adapter instance for: {source_name}")
        
        return adapter_instance
    
    def list_sources(self) -> List[str]:
        """
        List all registered data sources.
        
        Returns:
            List of data source names
        """
        return list(self._adapters.keys())
    
    def list_configured_sources(self) -> List[str]:
        """
        List data sources with loaded configurations.
        
        Returns:
            List of configured data source names
        """
        return list(self._configs.keys())
    
    def get_source_config(self, source_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific data source.
        
        Args:
            source_name: Name of the data source
            
        Returns:
            Configuration dictionary or None if not found
        """
        return self._configs.get(source_name)
    
    def test_connection(self, source_name: str) -> Dict[str, Any]:
        """
        Test connection to a data source.
        
        Args:
            source_name: Name of the data source
            
        Returns:
            Dictionary with test results
        """
        result = {
            'source': source_name,
            'success': False,
            'message': '',
            'supported_entities': []
        }
        
        try:
            adapter = self.get_adapter(source_name)
            success = adapter.test_connection()
            
            result['success'] = success
            result['message'] = 'Connection successful' if success else 'Connection failed'
            result['supported_entities'] = adapter.get_supported_entities()
            
        except Exception as e:
            result['message'] = f"Connection test failed: {str(e)}"
            logger.error(f"Connection test failed for {source_name}: {str(e)}")
        
        return result
    
    def test_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Test connections to all configured data sources.
        
        Returns:
            Dictionary mapping source names to test results
        """
        results = {}
        for source_name in self.list_configured_sources():
            results[source_name] = self.test_connection(source_name)
        return results
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """
        Validate all loaded configurations.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'valid': [],
            'invalid': [],
            'errors': {}
        }
        
        for source_name, config in self._configs.items():
            try:
                # Check required fields
                required_fields = ['api_token', 'base_url']
                missing_fields = [f for f in required_fields if not config.get(f)]
                
                if missing_fields:
                    validation_results['invalid'].append(source_name)
                    validation_results['errors'][source_name] = \
                        f"Missing required fields: {', '.join(missing_fields)}"
                else:
                    validation_results['valid'].append(source_name)
                    
            except Exception as e:
                validation_results['invalid'].append(source_name)
                validation_results['errors'][source_name] = str(e)
        
        return validation_results
    
    def clear_cache(self, source_name: Optional[str] = None):
        """
        Clear cached adapter instances.
        
        Args:
            source_name: Name of specific source to clear, or None for all
        """
        if source_name:
            if source_name in self._instances:
                del self._instances[source_name]
                logger.info(f"Cleared cache for: {source_name}")
        else:
            self._instances.clear()
            logger.info("Cleared all adapter instances from cache")


# Global registry instance
_global_registry = None


def get_registry(config_path: Optional[str] = None) -> DataSourceRegistry:
    """
    Get the global data source registry instance.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Global DataSourceRegistry instance
    """
    global _global_registry
    
    if _global_registry is None:
        _global_registry = DataSourceRegistry(config_path)
    
    return _global_registry
