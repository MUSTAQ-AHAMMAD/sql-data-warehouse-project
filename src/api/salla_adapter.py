"""
Salla API Adapter

Concrete implementation of GenericAPIAdapter for Salla e-commerce API.
"""

import os
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from .generic_api_adapter import GenericAPIAdapter, APIAdapterError

load_dotenv()


class SallaAPIAdapter(GenericAPIAdapter):
    """
    Salla API adapter implementing the GenericAPIAdapter interface.
    Provides integration with Salla e-commerce platform.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Salla API adapter.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
    
    def _setup_headers(self) -> Dict[str, str]:
        """
        Setup HTTP headers for Salla API requests.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def get_schema(self, entity_type: str) -> Dict[str, Any]:
        """
        Get the schema definition for a Salla entity type.
        
        Args:
            entity_type: Type of entity (orders, customers, products)
            
        Returns:
            Schema definition dictionary
        """
        schemas = {
            'orders': {
                'required_fields': ['id', 'customer', 'status', 'total', 'created_at'],
                'field_types': {
                    'id': 'int',
                    'customer': 'dict',
                    'status': 'string',
                    'total': 'dict',
                    'created_at': 'datetime'
                },
                'non_nullable_fields': ['id', 'status', 'total']
            },
            'customers': {
                'required_fields': ['id', 'email', 'first_name', 'last_name', 'created_at'],
                'field_types': {
                    'id': 'int',
                    'email': 'string',
                    'first_name': 'string',
                    'last_name': 'string',
                    'created_at': 'datetime'
                },
                'non_nullable_fields': ['id', 'email']
            },
            'products': {
                'required_fields': ['id', 'name', 'sku', 'price', 'created_at'],
                'field_types': {
                    'id': 'int',
                    'name': 'string',
                    'sku': 'string',
                    'price': 'dict',
                    'created_at': 'datetime'
                },
                'non_nullable_fields': ['id', 'name']
            }
        }
        
        return schemas.get(entity_type, {})
    
    def fetch_data(self, entity_type: str, page: int = 1,
                   per_page: Optional[int] = None) -> Dict:
        """
        Fetch data from Salla API for a specific entity type.
        
        Args:
            entity_type: Type of entity (orders, customers, products)
            page: Page number
            per_page: Number of items per page
            
        Returns:
            API response containing data
        """
        per_page = per_page or self.batch_size
        
        # Map entity types to Salla API endpoints
        endpoint_map = {
            'orders': '/orders',
            'customers': '/customers',
            'products': '/products'
        }
        
        endpoint = endpoint_map.get(entity_type)
        if not endpoint:
            raise APIAdapterError(
                f"Unsupported entity type: {entity_type}. "
                f"Supported types: {list(endpoint_map.keys())}"
            )
        
        params = {
            'page': page,
            'per_page': per_page
        }
        
        return self._make_request(endpoint, params=params)
    
    def _extract_data_from_response(self, response: Dict) -> List[Dict]:
        """
        Extract data array from Salla API response.
        
        Args:
            response: API response dictionary
            
        Returns:
            List of data records
        """
        # Salla API returns data in 'data' key
        return response.get('data', [])
    
    def _has_more_pages(self, response: Dict) -> bool:
        """
        Check if there are more pages to fetch in Salla API.
        
        Args:
            response: API response dictionary
            
        Returns:
            True if more pages exist, False otherwise
        """
        # Check pagination info
        pagination = response.get('pagination', {})
        
        # Salla uses 'hasMorePages' field
        if 'hasMorePages' in pagination:
            return pagination['hasMorePages']
        
        # Fallback: check if current page has data
        data = response.get('data', [])
        return len(data) > 0 and len(data) >= self.batch_size
    
    def get_supported_entities(self) -> List[str]:
        """
        Get list of supported entity types for Salla API.
        
        Returns:
            List of entity type names
        """
        return ['orders', 'customers', 'products']
