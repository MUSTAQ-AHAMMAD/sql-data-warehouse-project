"""
Generic API Adapter Interface

Provides a plugin-based architecture for integrating multiple data sources.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class APIAdapterError(Exception):
    """Custom exception for API adapter errors"""
    pass


class GenericAPIAdapter(ABC):
    """
    Abstract base class for API adapters.
    All API connectors should inherit from this class.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the API adapter with configuration.
        
        Args:
            config: Dictionary containing adapter configuration
                - api_token: Authentication token
                - base_url: Base URL for the API
                - batch_size: Number of items per request
                - max_retries: Maximum number of retry attempts
                - retry_delay: Delay between retries in seconds
        """
        self.api_token = config.get('api_token')
        self.base_url = config.get('base_url')
        self.batch_size = config.get('batch_size', 100)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 5)
        self.source_name = config.get('source_name', 'unknown')
        
        self._validate_config()
        self.headers = self._setup_headers()
    
    def _validate_config(self):
        """Validate required configuration parameters"""
        if not self.api_token:
            raise ValueError(f"API token is required for {self.source_name}")
        if not self.base_url:
            raise ValueError(f"Base URL is required for {self.source_name}")
    
    @abstractmethod
    def _setup_headers(self) -> Dict[str, str]:
        """
        Setup HTTP headers for API requests.
        Must be implemented by subclasses.
        
        Returns:
            Dictionary of HTTP headers
        """
        pass
    
    @abstractmethod
    def get_schema(self, entity_type: str) -> Dict[str, Any]:
        """
        Get the schema definition for an entity type.
        
        Args:
            entity_type: Type of entity (e.g., 'orders', 'customers')
            
        Returns:
            Schema definition dictionary
        """
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, 
                     method: str = 'GET', data: Optional[Dict] = None) -> Dict:
        """
        Make HTTP request with retry logic and rate limiting.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            method: HTTP method (GET, POST, etc.)
            data: Request body data
            
        Returns:
            JSON response as dictionary
            
        Raises:
            APIAdapterError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Making {method} request to {url} with params {params}")
            
            if method == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, params=params, 
                                       json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                raise requests.exceptions.RequestException("Rate limited")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            raise APIAdapterError(f"Failed to fetch data from {self.source_name}: {str(e)}")
    
    @abstractmethod
    def fetch_data(self, entity_type: str, page: int = 1, 
                   per_page: Optional[int] = None) -> Dict:
        """
        Fetch data for a specific entity type.
        
        Args:
            entity_type: Type of entity to fetch
            page: Page number
            per_page: Number of items per page
            
        Returns:
            API response containing data
        """
        pass
    
    def fetch_all_pages(self, entity_type: str, max_pages: Optional[int] = None,
                       transform_func: Optional[Callable] = None) -> List[Dict]:
        """
        Fetch all pages of data for a specific entity type.
        
        Args:
            entity_type: Type of entity to fetch
            max_pages: Maximum number of pages to fetch
            transform_func: Optional function to transform each record
            
        Returns:
            List of all records from all pages
        """
        all_records = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            try:
                logger.info(f"Fetching {entity_type} page {page} from {self.source_name}")
                response = self.fetch_data(entity_type, page=page)
                
                # Extract data from response
                data = self._extract_data_from_response(response)
                if not data:
                    logger.warning(f"No data returned for {entity_type} page {page}")
                    break
                
                # Apply transformation if provided
                if transform_func:
                    data = [transform_func(record) for record in data]
                
                all_records.extend(data)
                
                # Check if there are more pages
                if not self._has_more_pages(response):
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limiting delay
                
            except Exception as e:
                logger.error(f"Error fetching page {page}: {str(e)}")
                raise APIAdapterError(f"Failed to fetch {entity_type}: {str(e)}")
        
        logger.info(f"Fetched total of {len(all_records)} {entity_type} from {self.source_name}")
        return all_records
    
    @abstractmethod
    def _extract_data_from_response(self, response: Dict) -> List[Dict]:
        """
        Extract data array from API response.
        Different APIs have different response structures.
        
        Args:
            response: API response dictionary
            
        Returns:
            List of data records
        """
        pass
    
    @abstractmethod
    def _has_more_pages(self, response: Dict) -> bool:
        """
        Check if there are more pages to fetch.
        
        Args:
            response: API response dictionary
            
        Returns:
            True if more pages exist, False otherwise
        """
        pass
    
    def validate_response(self, response: Dict, entity_type: str) -> bool:
        """
        Validate API response structure.
        
        Args:
            response: API response to validate
            entity_type: Type of entity
            
        Returns:
            True if valid, False otherwise
        """
        try:
            data = self._extract_data_from_response(response)
            if data is None:
                return False
            
            # Validate against schema if available
            schema = self.get_schema(entity_type)
            if schema and data:
                # Basic schema validation
                required_fields = schema.get('required_fields', [])
                sample_record = data[0] if data else {}
                
                for field in required_fields:
                    if field not in sample_record:
                        logger.warning(f"Missing required field: {field}")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Response validation failed: {str(e)}")
            return False
    
    def get_supported_entities(self) -> List[str]:
        """
        Get list of supported entity types for this adapter.
        
        Returns:
            List of entity type names
        """
        return []
    
    def test_connection(self) -> bool:
        """
        Test API connection and authentication.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to fetch first page of a supported entity
            entities = self.get_supported_entities()
            if entities:
                response = self.fetch_data(entities[0], page=1, per_page=1)
                return self.validate_response(response, entities[0])
            return False
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
